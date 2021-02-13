import logging
import time
from multiprocessing import Process
from typing import List

import cflib.crtp
from cflib.crtp.radiodriver import RadioManager
from clients.crazyradio_client import CrazyradioClient
from metaclasses.singleton import Singleton
from services.communications import CommunicationService


class CrazyradioController(metaclass=Singleton):

    def __init__(self) -> None:
        cflib.crtp.init_drivers(enable_debug_driver=False)

    def launchServer(self):

        while not self.isDongleConnected():
            logging.error(
                'Crazyradio Dongle is not connected. Retrying in 3 secondes.')
            time.sleep(3)

        while True:
            interfaces = self.getAvailableInterfaces()
            if len(interfaces) > 0:
                break
            logging.error(f'No drones found nearby. Retrying in 3 secondes.')
            time.sleep(3)

        for interface in interfaces:
            logging.info(
                f'New Crazyradio found at interface {interface}')
            client = CrazyradioClient(interface)
            CommunicationService.crazyRadioClients.add(client)

    def isDongleConnected(self) -> bool:
        crazyradioDriver = RadioManager()
        try:
            crazyradioDriver.open(0)
            return True
        except:
            return False

    def getAvailableInterfaces(self) -> List:
        return cflib.crtp.scan_interfaces()

    def launch(self) -> Process:
        process = Process(target=self.launchServer)
        process.start()
        return process
