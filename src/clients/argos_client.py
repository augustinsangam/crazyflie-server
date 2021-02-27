import socket
from threading import Thread

from models.connection import Connection, HandlerType


class ArgosClient:
    def __init__(self) -> None:
        self.connection = Connection()

    def connect(self, socket) -> None:
        self.socket = socket
        Thread(target=self.handleCommunications).start()

    def handleCommunications(self):
        self.connection.callAllCallbacks(HandlerType.connection)
        try:
            while True:
                message = self.socket.recv(1024)
                if message == b'':
                    self.socket.close()
                    break
                self.connection.callAllCallbacks(
                    HandlerType.message, message)
        except Exception as e:
            self.socket.close()
            self.connection.callAllCallbacks(HandlerType.error, e)
        finally:
            self.connection.callAllCallbacks(HandlerType.disconnection)

    def closeClient(self):
        self.socket.shutdown(socket.SHUT_RDWR)
