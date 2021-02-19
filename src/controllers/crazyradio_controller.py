import logging
import subprocess
import time
from os import getenv
from threading import Thread
from typing import List

import cflib.crtp
from cflib.crtp.radiodriver import RadioManager
from clients.crazyradio_client import CrazyradioClient
from metaclasses.singleton import Singleton
from services.communications import CommunicationService
from services.drones import DronesService


class CrazyradioController(metaclass=Singleton):

    def __init__(self) -> None:
        cflib.crtp.init_drivers(enable_debug_driver=False)
        pass

    def launchServer(self):

        while not self.isDongleConnected():
            logging.error(
                'Crazyradio Dongle is not connected. Retrying in 3 secondes.')
            time.sleep(3)

        logging.info(f"Successfully connected to Crazyradio Dongle")

        cf2_bin = getenv('CF2_BIN')
        if cf2_bin:
            logging.critical(
                f'Flashing drone using the cfloader. Ensure yourself to have drones in Bootloader mode')
            subprocess.call(['python3', '-m', 'cfloader', 'flash',
                             cf2_bin, 'stm32-fw'])

        while True:
            interfaces = self.getAvailableInterfaces()

            if len(interfaces) > 0:
                break
            logging.error(f'No drones found nearby. Retrying in 3 secondes.')
            time.sleep(3)

        for interface in interfaces:
            self.handleClient(interface)

    def handleClient(self, interface):
        logging.info(
            f'New Crazyradio found at interface {interface}')
        try:
            client = CrazyradioClient(interface)
            CommunicationService.crazyRadioClients.add(client)

            def onClientDisconnect():
                droneName: str = client.drone['name']
                DronesService.removeDrove(droneName)
                CommunicationService.sendToDashboardClients({
                    "type": "disconnect",
                    "data": {
                        "name": droneName
                    }
                })

            client._cf.connection_lost.add_callback(onClientDisconnect)
        except:
            pass

    def isDongleConnected(self) -> bool:
        crazyradioDriver = RadioManager()
        try:
            crazyradioDriver.open(0)
            return True
        except:
            return False

    def getAvailableInterfaces(self) -> List:
        return cflib.crtp.scan_interfaces()

    def launch(self) -> Thread:
        thread = Thread(target=self.launchServer)
        thread.start()
        return thread
