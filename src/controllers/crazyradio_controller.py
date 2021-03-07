import json
import logging
import subprocess
import time
import struct
from io import StringIO
from os import getenv
from threading import Thread
from typing import Any, List, Set, Union

import cflib.crtp
from cflib.crtp.radiodriver import RadioManager
from src.clients.crazyradio_client import CrazyradioClient
from src.metaclasses.singleton import Singleton
from src.models.connection import HandlerType
from src.models.drone import Drone
from src.models.message import Message
from src.services.communications import CommunicationService
from src.services.drones_set import DronesSet


class CrazyradioController(metaclass=Singleton):
    running = True
    dronesSet = DronesSet()
    clients: Set[CrazyradioClient] = set()

    @staticmethod
    def launch() -> Thread:
        """Launches a thread in witch the craziradio controller will start, and return that thread.

        """
        thread = Thread(target=CrazyradioController.launchServer)
        thread.start()
        return thread

    @staticmethod
    def launchServer():
        """Start the server. Scans for the dongle and wait untill its is connected.
        Scans for interface (drones) then create a client for each interface found.

        """
        cflib.crtp.init_drivers(enable_debug_driver=False)
        while not CrazyradioController.isDongleConnected() and CrazyradioController.running:
            logging.error(
                'Crazyradio Dongle is not connected. Retrying in 3 seconds.')
            time.sleep(3)

        if not CrazyradioController.running:
            return

        logging.info(f"Successfully connected to Crazyradio Dongle")

        cf2_bin = getenv('CF2_BIN')
        if cf2_bin:
            logging.critical(
                f'Flashing drone using the cfloader. Ensure yourself to have drones in Bootloader mode')
            subprocess.call(['python3', '-m', 'cfloader', 'flash',
                             cf2_bin, 'stm32-fw'])

        interfaces = []
        while CrazyradioController.running:
            interfaces = CrazyradioController.getAvailableInterfaces()

            if len(interfaces) > 0:
                break
            logging.error(
                f'No drones found nearby. Retrying in 3 seconds.')
            time.sleep(3)

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
        # TODO revoir l'utilite
        return cflib.crtp.scan_interfaces()

    @staticmethod
    def stopServer():
        """Close the controller by closing every client.

        """
        CrazyradioController.running = False
        for client in CrazyradioController.clients:
            client.closeClient()

    @staticmethod
    def handleClient(interface):
        """Creates a client witch will listen to the new connection. Callbacks handlers are set for every event.

          @param interface: the interface of the new connection.
        """
        client = CrazyradioClient()
        CrazyradioController.clients.add(client)
        handlers = [
            [HandlerType.connection, CrazyradioController.onClientConnect],
            [HandlerType.disconnection, CrazyradioController.onClientDisconnect],
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

    @staticmethod
    def onClientConnect(client: CrazyradioClient) -> None:
        """Called by a client when it connects to its interface.

          @param client: the client witch called the function.
        """
        logging.info(f'New Crazyradio client connected on uri {client.uri}')

    @staticmethod
    def onClientDisconnect(client: CrazyradioClient) -> None:
        """Called by a client when it disconnects from its interface. It send a message to the \
            dashboards to inform the disconnection only if the server is running.

          @param client: the client witch called the function.
        """
        logging.info(f'Crazyradio client disconnected from uri {client.uri}')
        CrazyradioController.clients.remove(client)
        if CrazyradioController.running:
            drone: Drone = CrazyradioController.dronesSet.getDrone(client.uri)
            CommunicationService().sendToDashboardController({
                "type": "disconnect",
                "data": {
                    "name": drone['name']
                }
            })
        CrazyradioController.dronesSet.removeDrone(client.uri)

    @staticmethod
    def onClientReceivedMessage(client: CrazyradioClient, data) -> None:
        """Called by a client when it receives a message. The message parsed as json.
        It updates the drone stored status, then sends the message to the dasboards.

          @param client: the client witch called the function.
          @param message: the message in bytes received by the client.
        """
        droneIdentifier = CrazyradioController.getDroneIdentifier(client.uri)
        try:
            message = struct.unpack("<Qfffff??", data)
            drone = Drone()
            drone['timestamp'] = message[0]
            drone['speed'] = message[1]
            drone['battery'] = message[2]
            drone['position'] = [message[3], message[4], message[5]]
            drone['flying'] = message[6]
            drone['ledOn'] = message[7]
            drone['real'] = True
            CrazyradioController.dronesSet.setDrone(client.uri, drone)

            # parsedMessage: Message = json.load(StringIO(message))
        except ValueError:
            logging.error(
                f'Crazyradio client {droneIdentifier} receive a wrong json format : {message}')
        else:
            logging.info(
                f'Crazyradio client {droneIdentifier} received message : {message}')
            # if parsedMessage['type'] != 'pulse':
            # return
            # droneData: dict = parsedMessage['data']
            # Force Crazyradio drone to be real
            # droneData = {**droneData, "real": True}
            # drone = Drone(**droneData)
            CrazyradioController.dronesSet.setDrone(client.uri, drone)
            CommunicationService().sendToDashboardController(
                '\{\"type\":"pulse","data":' + drone + '}')

    @staticmethod
    def onClientRaisedError(client: CrazyradioClient, error: Exception) -> None:
        """Called when a client raises an error while it waits for messages.

          @param client: the client witch called the function.
          @param error: the exception  raised by the client.
        """
        logging.info(
            f'ARGoS Crazyradio connected on uri {client.uri} raised an error:\n{error}')

    @staticmethod
    def sendMessage(message: Message) -> None:
        """Sends the specified message to the correct drone. doesn't sends anything if the requested drone doesn't exist.

          @param message: the message to send.
        """

        if message['type'] == 'startMission':
            missionRequestData: dict = message['data']
            if missionRequestData['type'] == 'fake':
                pass
            elif missionRequestData['type'] == 'argos':
                pass
            return

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
        """Sends the specified message to the specified client after converting it from json to string.

          @param client: the socket to send the message.
          @param message: the message to send.
        """
        messageStr = json.dumps(message)
        client.sendMessage(messageStr)

    @staticmethod
    def getDroneIdentifier(uri: str) -> Union[Drone, Any]:
        """Find the drone associated with the specified uri. If the drone name isn't yet registered, the uri is returned.

          @param uri: the uri of the searched drone.
        """
        drone: Drone = CrazyradioController.dronesSet.getDrone(uri)
        return drone['name'] if drone else uri
