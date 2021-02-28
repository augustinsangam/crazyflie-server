import json
import logging
import subprocess
import time
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
        thread = Thread(target=CrazyradioController.launchServer)
        thread.start()
        return thread

    @staticmethod
    def launchServer():
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
        crazyradioDriver = RadioManager()
        try:
            crazyradioDriver.open(0)
            return True
        except:
            return False

    @staticmethod
    def getAvailableInterfaces() -> List:
        return cflib.crtp.scan_interfaces()

    @staticmethod
    def stopServer():
        CrazyradioController.running = False
        for client in CrazyradioController.clients:
            client.closeClient()

    @staticmethod
    def handleClient(interface):
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
                client=client
            )
        uri: str = interface[0]
        client.connect(uri)

    @staticmethod
    def onClientConnect(client: CrazyradioClient) -> None:
        logging.info(f'New Crazyradio client connected on uri {client.uri}')

    @staticmethod
    def onClientDisconnect(client: CrazyradioClient) -> None:
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
    def onClientReceivedMessage(message: str, client: CrazyradioClient) -> None:
        droneIdentifier = CrazyradioController.getDroneIdentifier(client.uri)
        try:
            parsedMessage: Message = json.load(StringIO(message))
        except ValueError:
            logging.error(
                f'Crazyradio client {droneIdentifier} receive a wrong json format : {message}')
        else:
            logging.info(
                f'Crazyradio client {droneIdentifier} received message : {message}')
            if parsedMessage['type'] != 'pulse':
                return
            droneData: dict = parsedMessage['data']
            # Force Crazyradio drone to be real
            droneData = {**droneData, "real": True}
            drone = Drone(**droneData)
            CrazyradioController.dronesSet.setDrone(client.uri, drone)
            CommunicationService().sendToDashboardController(parsedMessage)

    @staticmethod
    def onClientRaisedError(error: Exception, client: CrazyradioClient) -> None:
        logging.info(
            f'ARGoS Crazyradio connected on uri {client.uri} raised an error:\n{error}')

    @staticmethod
    def sendMessage(message: Message) -> None:
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
        messageStr = json.dumps(message)
        client.sendMessage(messageStr)

    @staticmethod
    def getDroneIdentifier(uri: str) -> Union[Drone, Any]:
        drone: Drone = CrazyradioController.dronesSet.getDrone(uri)
        return drone['name'] if drone else uri
