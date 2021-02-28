import socket
from threading import Thread

from flask_threaded_sockets.websocket import WebSocket

from src.models.connection import Connection, HandlerType


class ArgosClient:
    def __init__(self) -> None:
        self.socket = None
        self.connection = Connection()

    def connect(self, webSocket: WebSocket) -> None:
        self.socket = webSocket
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
