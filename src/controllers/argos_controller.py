import logging
import socket
from threading import Thread

from clients.argos_client import ArgosClient
from metaclasses.singleton import Singleton
from services.communications import CommunicationService
from services.drones import DronesService


class ArgosController(metaclass=Singleton):
    TCP_IP = '127.0.0.1'
    TCP_PORT = 3995
    BUFFER_SIZE = 20
    N_MAX_DRONES = 10

    def launchServer(self):
        TCPServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        TCPServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        TCPServer.bind((ArgosController.TCP_IP, ArgosController.TCP_PORT))
        TCPServer.listen(ArgosController.N_MAX_DRONES)

        while True:
            clientSocket, addr = TCPServer.accept()
            Thread(target=self.handleClient, args=(clientSocket, addr)).start()

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
