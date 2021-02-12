#!/usr/bin/env python3

import socket
import threading

from clients.argos import ArgosClient
from metaclasses.singleton import Singleton
from services.communications import CommunicationService
from utils.logger import Logger


class ArgosController(metaclass=Singleton):
    TCP_IP = '127.0.0.1'
    TCP_PORT = 3995
    BUFFER_SIZE = 20
    N_MAX_DRONES = 2

    logger = Logger()

    def launchServer(self):
        TCPServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        TCPServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        TCPServer.bind((ArgosController.TCP_IP, ArgosController.TCP_PORT))
        TCPServer.listen(ArgosController.N_MAX_DRONES)

        while True:
            clientSocket, addr = TCPServer.accept()
            ArgosController.logger.log(
                f'New simulated drone connected at {addr}')
            client = ArgosClient(clientSocket)
            CommunicationService.argosClients.add(client)

    def launch(self):
        thread = threading.Thread(target=self.launchServer)
        thread.daemon = True
        thread.start()
