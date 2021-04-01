import socket
from threading import Thread

from flask_threaded_sockets.websocket import WebSocket

from src.models.connection import Connection, HandlerType


class ArgosClient:
    def __init__(self) -> None:
        self.socket = None
        self.connection = Connection()

    def connect(self, webSocket: WebSocket) -> None:
        """Assign the client to the specified websocket and start a thread to
        handle the communication.

          @param webSocket: the socket on witch the client is connected.
        """
        self.socket = webSocket
        Thread(target=self.handleCommunications).start()

    def handleCommunications(self):
        """Listen on the socket for messages. It closes the client if it
        receive an empty string.

        """
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
        """Force close the connection. Called by the sigint handler.

        """
        self.socket.shutdown(socket.SHUT_RDWR)
