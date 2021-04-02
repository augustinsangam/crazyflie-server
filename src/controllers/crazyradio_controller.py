import logging
import struct
import subprocess
import threading
import time
from threading import Thread
from typing import Any, List, Set, Union

import cflib.crtp
from cflib.crtp.radiodriver import RadioManager

from src.models.mission import Vec2
from src.models.software_update import LoadProjectData, ProjectType, LogType, \
    LoadProjectLog
from src.services.mission_handler import MissionHandler
from src.clients.crazyradio_client import CrazyradioClient
from src.metaclasses.singleton import Singleton
from src.models.connection import HandlerType
from src.models.drone import Drone
from src.models.message import Message
from src.services.communications import CommunicationService
from src.services.drones_set import DronesSet
from src.utils.timestamp import getTimestamp


class CrazyradioController(metaclass=Singleton):
    running = True
    dronesSet = DronesSet()
    clients: Set[CrazyradioClient] = set()
    missionHandler: MissionHandler
    projectCurrentlyLoading = False
    FIRST_DRONE_ADDRESS = 0xE7E7E7E701
    MAX_DRONE_NUMBER = 2

    @staticmethod
    def launch() -> Thread:
        """Launches a thread in witch the crazyradio controller will start,
        and return that thread.

        """
        thread = Thread(target=CrazyradioController.launchServer)
        thread.start()
        return thread

    @staticmethod
    def launchServer():
        """Start the server. Scans for the dongle and wait until its is
        connected. Scans for interface (drones) then create a client for each
        interface found.

        """
        cflib.crtp.init_drivers(enable_debug_driver=False)
        while not CrazyradioController.isDongleConnected() and CrazyradioController.running:
            logging.warning(
                'Crazyradio PA dongle is not connected. Retrying in 5 seconds.')
            time.sleep(5)

        if not CrazyradioController.running:
            return

        logging.info(f"Successfully connected to Crazyradio Dongle")

        interfaces = []
        while CrazyradioController.running:
            interfaces = CrazyradioController.getAvailableInterfaces()

            if len(interfaces) > 0:
                break
            logging.warning(
                f'No drones found nearby. Retrying in 5 seconds.')
            time.sleep(5)

        if not CrazyradioController.running:
            return

        for interface in interfaces:
            CrazyradioController.handleClient(interface)

    @staticmethod
    def isDongleConnected() -> bool:
        """Check if the dongle is connected.

        """
        crazyradioDriver = RadioManager()
        try:
            crazyradioDriver.open(0)
            return True
        except:
            return False

    @staticmethod
    def getAvailableInterfaces() -> List:
        """
        TODO
        """
        available = []
        first = CrazyradioController.FIRST_DRONE_ADDRESS
        last = CrazyradioController.FIRST_DRONE_ADDRESS + CrazyradioController.MAX_DRONE_NUMBER

        for address in range(first, last):
            available = [
                *available,
                *cflib.crtp.scan_interfaces(address)
            ]
        return available

    @staticmethod
    def stopServer():
        """Close the controller by closing every client.

        """
        CrazyradioController.running = False
        for client in CrazyradioController.clients:
            client.closeClient()

    @staticmethod
    def handleClient(interface):
        """Creates a client witch will listen to the new connection.
        Callbacks handlers are set for every event.

          @param interface: the interface of the new connection.
        """
        client = CrazyradioClient()
        CrazyradioController.clients.add(client)
        handlers = [
            [HandlerType.connection, CrazyradioController.onClientConnect],
            [HandlerType.disconnection,
             CrazyradioController.onClientDisconnect],
            [HandlerType.message, CrazyradioController.onClientReceivedMessage],
            [HandlerType.error, CrazyradioController.onClientRaisedError],
        ]
        for handlerType, handlerFunc in handlers:
            client.connection.addCallback(
                handlerType,
                handlerFunc,
                client
            )
        uri: str = interface[0]
        client.connect(uri)
        newDrone = Drone(
            name=uri,
            timestamp=getTimestamp(),
            speed=0.0,
            battery=0,
            position=[0.0, 0.0, 0.0],
            yaw=0.0,
            ranges=[0, 0, 0, 0],
            flying=False,
            ledOn=False,
            real=True
        )
        CrazyradioController.dronesSet.setDrone(uri, newDrone)

    @staticmethod
    def onClientConnect(client: CrazyradioClient) -> None:
        """Called by a client when it connects to its interface.

          @param client: the client witch called the function.
        """
        logging.info(f'New Crazyradio client connected on uri {client.uri}')

    @staticmethod
    def onClientDisconnect(client: CrazyradioClient) -> None:
        """Called by a client when it disconnects from its interface. It send
        a message to the dashboards to inform the disconnection only if the
        server is running.

          @param client: the client witch called the function.
        """
        logging.info(f'Crazyradio client disconnected from uri {client.uri}')
        if CrazyradioController.running:
            CrazyradioController.clients.remove(client)
            drone: Drone = CrazyradioController.dronesSet.getDrone(client.uri)
            CommunicationService().sendToDashboardController(
                Message(
                    type="disconnect",
                    data={
                        "name": drone['name']
                    }
                )
            )
            CrazyradioController.dronesSet.removeDrone(client.uri)

    @staticmethod
    def onClientReceivedMessage(client: CrazyradioClient, data) -> None:
        """Called by a client when it receives a message. The message parsed
        as json. It updates the drone stored status, then sends the message
        to the dashboards.

          @param client: the client witch called the function.
          @param data: the data of the message in bytes received by the client.
        """
        droneIdentifier = CrazyradioController.getDroneIdentifier(client.uri)
        try:

            (code,) = struct.unpack_from("<h", data, 0)
            print("le code en bas")
            print(code)
            drone = CrazyradioController.dronesSet.getDrone(client.uri)
            if not drone:
                logging.error("Unknown drone received a message")
                return

            if code == 0:
                (cd, battery) = struct.unpack("<hf", data)
                print(f"Received : {cd}, {battery}")
                drone = {**drone, "battery": battery}
            elif code == 1:
                (cd, timestamp) = struct.unpack("<hQ", data)
                print(f"Received : {cd}, {timestamp}")
                drone = {**drone, "timestamp": getTimestamp()}
            elif code == 2:
                (cd, speed) = struct.unpack("<hf", data)
                print(f"Received : {cd}, {speed}")
                drone = {**drone, "speed": speed}
            elif code == 3:
                (cd, positionX, positionY, positionZ) = struct.unpack("<hfff",
                                                                      data)
                print(f"Received : {cd}, {positionX}, {positionY}, {positionZ}")
                drone = {**drone, "position": [positionX, positionY, positionZ]}
            elif code == 4:
                (cd, front, left, back, right, up) = struct.unpack("<hHHHHH",
                                                                   data)
                print(
                    f"Received : {cd}, {front}, {left}, {back}, {right}, {up}")
                drone = {**drone, "ranges": [front, left, back, right]}
            elif code == 5:
                (cd, flying, ledOn) = struct.unpack("<h??", data)
                print(f"Received : {cd}, {flying}, {ledOn}")
                drone = {**drone, "ledOn": ledOn, "flying": flying}
            else:
                print("Unknown code")

            # parsedMessage: Message = json.load(StringIO(message))
        except ValueError:
            logging.error(
                f'Crazyradio client {droneIdentifier} receive a wrong struct '
                f'format : {data}')
        else:
            logging.debug(
                f'Crazyradio client {droneIdentifier} received message : {data}')
            # if parsedMessage['type'] != 'pulse':
            # return
            # droneData: dict = parsedMessage['data']
            # Force Crazyradio drone to be real
            # droneData = {**droneData, "real": True}
            # drone = Drone(**droneData)
            # CrazyradioController.dronesSet.setDrone(client.uri, drone)
            # CrazyradioController.missionHandler.onReceivedPositionAndRange(
            #     drone['name'],
            #     Vec2(x=drone['position'][0], y=drone['position'][1]),
            #     drone['yaw'],
            #     drone['ranges'][0:4]
            # )
            CommunicationService().sendToDashboardController(
                Message(
                    type="pulse",
                    data=drone
                )
            )

    @staticmethod
    def onClientRaisedError(client: CrazyradioClient, error: Exception) -> None:
        """Called when a client raises an error while it waits for messages.

          @param client: the client witch called the function.
          @param error: the exception  raised by the client.
        """
        logging.info(
            f'ARGoS Crazyradio connected on uri {client.uri} raised an error:\n{error}')

    @staticmethod
    def onControllerReceivedMessage(message: Message):
        """Decide what to do with the given message. It can start a mission
        or send the message as is to the clients. @param message: the message
        received.
        """
        if message['type'] == 'startMission':
            missionRequestData: dict = message['data']
            if missionRequestData['type'] == 'crazyradio':
                CrazyradioController.startMission()
        elif message['type'] == 'loadProject':
            loadProjectData = LoadProjectData(**message['data'])
            CrazyradioController.loadProject(loadProjectData)

    @staticmethod
    def sendMessage(message: Message) -> None:
        """Sends the specified message to the correct drone. doesn't sends
        anything if the requested drone doesn't exist.

          @param message: the message to send.
        """
        uri = message['data']['name']
        if uri == '*':
            for client in CrazyradioController.clients:
                CrazyradioController.sendMessageToClient(client, message)
            return

        client = None
        for c in CrazyradioController.clients:
            if c.uri == uri:
                client = c
                break
        if not client:
            return
        CrazyradioController.sendMessageToClient(client, message)

    @staticmethod
    def sendMessageToClient(client: CrazyradioClient, message: Message):
        """Sends the specified message to the specified client after
        converting it from json to string.

          @param client: the socket to send the message.
          @param message: the message to send.
        """
        client.sendMessage(message)

    @staticmethod
    def getDroneIdentifier(uri: str) -> Union[Drone, Any]:
        """Find the drone associated with the specified uri. If the drone
        name isn't yet registered, the uri is returned.

          @param uri: the uri of the searched drone.
        """
        drone: Drone = CrazyradioController.dronesSet.getDrone(uri)
        return drone['name'] if drone else uri

    @staticmethod
    def startMission():
        """Start a mission. Order drones to takeoff and initialize a mission
        handler.

        """
        CrazyradioController.sendMessage(
            Message(
                type='startMission',
                data={"name": "*"}
            )
        )
        if CrazyradioController.missionHandler is not None:
            CrazyradioController.missionHandler.endMission()

        CrazyradioController.missionHandler = MissionHandler(
            dronesSet=CrazyradioController.dronesSet,
            missionType='crazyradio',
            sendMessageCallable=lambda
                m: CommunicationService().sendToDashboardController(m)
        )

    @staticmethod
    def stopMission():
        CrazyradioController.sendMessage(
            Message(
                type='stopMission',
                data={"name": "*"}
            )
        )
        if CrazyradioController.missionHandler is not None:
            CrazyradioController.missionHandler.endMission()

        CrazyradioController.missionHandler.endMission()

    @staticmethod
    def cloadAll(uris: List[str], cf2_bin: str):
        for uri in uris:
            logMessage = f'Flashing drone at uri {uri}'
            logging.critical(logMessage)
            CrazyradioController.sendLogToDashboard('info', logMessage)
            subprocess.call(['python3', '-m', 'cfloader', 'flash',
                             cf2_bin, 'stm32-fw', '-w', uri])

    @staticmethod
    def sendLogToDashboard(logType: LogType, log: str):
        message = Message(
            type='loadProjectLog',
            data=LoadProjectLog(
                log=log,
                type=logType
            )
        )
        CommunicationService().sendToDashboardController(message)

    @staticmethod
    def loadProject(loadProjectData: LoadProjectData):
        if CrazyradioController.projectCurrentlyLoading:
            return

        CrazyradioController.projectCurrentlyLoading = True

        projectType = loadProjectData['type']
        code = None
        if 'code' in loadProjectData:
            code = loadProjectData['code']

        t = threading.Thread(target=CrazyradioController.loadProjectThread,
                             args=(projectType, code))
        t.start()

    @staticmethod
    def loadProjectThread(projectType: ProjectType, code=None):
        # TODO
        logging.info(f'Loafing {projectType} with code {code}')
        # At the end
        CrazyradioController.projectCurrentlyLoading = False
