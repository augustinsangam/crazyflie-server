import logging
import socket
from threading import Thread

import flask_threaded_sockets

from clients.argos_client import ArgosClient
from metaclasses.singleton import Singleton
from services.communications import CommunicationService
from services.drones import DronesService


class ArgosController(metaclass=Singleton):
    TCP_IP = '0.0.0.0'
    TCP_PORT = 3995
    BUFFER_SIZE = 20
    N_MAX_DRONES = 10
    TCPServer = None
    running = True

    def launchServer(self):
        TCPServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        TCPServer.setblocking(False)
        TCPServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        TCPServer.bind((ArgosController.TCP_IP, ArgosController.TCP_PORT))
        TCPServer.listen(ArgosController.N_MAX_DRONES)
        ArgosController.TCPServer = TCPServer

        while ArgosController.running:
            try:
                clientSocket, addr = TCPServer.accept()
                Thread(target=self.handleClient, args=(
                    clientSocket, addr)).start()
            except:
                pass

    def handleClient(self, clientSocket, addr):
        logging.info(
            f'New simulated drone connected at {addr}')
        try:
            client = ArgosClient(clientSocket)
            CommunicationService.argosClients.add(client)
            client.thread.join()
        finally:
            CommunicationService.argosClients.remove(client)
            droneName: str = client.drone['name']
            DronesService.removeDrove(droneName)
            if ArgosController.running:
                CommunicationService.sendToDashboardClients({
                    "type": "disconnect",
                    "data": {
                        "name": droneName
                    }
                })

    def launch(self) -> Thread:
        thread = Thread(target=self.launchServer)
        thread.start()
        return thread

    def stopServer():
        for client in CommunicationService.argosClients:
            client.closeClient()
        ArgosController.running = False
        ArgosController.TCPServer.close()
        # shutdown(socket.SHUT_RDWR)
