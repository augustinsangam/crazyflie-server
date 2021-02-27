import json
import logging
import subprocess
import time
from io import StringIO
from os import getenv
from threading import Thread
from typing import Any, List, Set, Union

import cflib.crtp
import clients
from cflib.crtp.radiodriver import RadioManager
from clients.crazyradio_client import CrazyradioClient
from metaclasses.singleton import Singleton
from models.connection import HandlerType
from models.drone import Drone
from models.message import Message
from services.communications import CommunicationService
from services.drones_set import DronesSet


class CrazyradioController(metaclass=Singleton):

    running = True
    dronesSet = DronesSet()
    clients: Set[CrazyradioClient] = set()

    def __init__(self) -> None:
        cflib.crtp.init_drivers(enable_debug_driver=False)
        pass

    def launch(self) -> Thread:
        thread = Thread(target=self.launchServer)
        thread.start()
        return thread

    def launchServer(self):
        while not self.isDongleConnected() and CrazyradioController.running:
            logging.error(
                'Crazyradio Dongle is not connected. Retrying in 3 secondes.')
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

        while CrazyradioController.running:
            interfaces = self.getAvailableInterfaces()

            if len(interfaces) > 0:
                break
            logging.error(
                f'No drones found nearby. Retrying in 3 secondes.')
            time.sleep(3)

        if not CrazyradioController.running:
            return

        for interface in interfaces:
            self.handleClient(interface)

    def isDongleConnected(self) -> bool:
        crazyradioDriver = RadioManager()
        try:
            crazyradioDriver.open(0)
            return True
        except:
            return False

    def getAvailableInterfaces(self) -> List:
        return cflib.crtp.scan_interfaces()

    def stopServer():
        CrazyradioController.running = False
        for client in CrazyradioController.clients:
            client.closeClient()

    def handleClient(self, interface):
        client = CrazyradioClient()
        CrazyradioController.clients.add(client)
        client.connection.addCallback(
            HandlerType.connection, CrazyradioController.onClientConnect, client=client)
        client.connection.addCallback(
            HandlerType.disconnection, CrazyradioController.onClientDisconnect, client=client)
        client.connection.addCallback(
            HandlerType.message, CrazyradioController.onClientReceivedMessage, client=client)
        client.connection.addCallback(
            HandlerType.error, CrazyradioController.onClientRaisedError, client=client)
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
        except:
            logging.error(
                f'Crazyradio client {droneIdentifier} receive a wrong json format : {message}')
        else:
            logging.info(
                f'Crazyradio client {droneIdentifier} received message : {message}')
            if parsedMessage['type'] != 'pulse':
                return
            drone: Drone = parsedMessage['data']
            # Force Crazyradio drone to be real
            drone = {**drone, "real": True}
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
    def sendMessageToClient(client, message: Message):
        messageStr = json.dumps(message)
        client.sendMessage(messageStr)

    @staticmethod
    def getDroneIdentifier(uri) -> Union[Drone, Any]:
        drone: Drone = CrazyradioController.dronesSet.getDrone(uri)
        return drone['name'] if drone else uri
