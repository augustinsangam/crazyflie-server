import logging
from threading import Thread

from flask_threaded_sockets.websocket import WebSocket
from src.models.connection import Connection, HandlerType


class DashboardClient:

    def __init__(self) -> None:
        self.socket = None
        self.thread = None
        self.connection = Connection()

    def connect(self, socket) -> None:
        """Assing the client to the specified socket and start a thread to handle the communication.

          @param socket: the socket on witch the client is connected.
        """
        self.socket: WebSocket = socket
        Thread(target=self.handleCommunications).start()

    def handleCommunications(self) -> None:
        """Listen for message on the socket while the connection is active. 

        """
        self.connection.callAllCallbacks(HandlerType.connection)
        try:
            while not self.socket.closed:
                message = self.socket.receive()
                self.connection.callAllCallbacks(
                    HandlerType.message, message)
        except Exception as e:
            logging.error(e)
            self.socket.close()
            self.connection.callAllCallbacks(HandlerType.error, e)
        finally:
            self.connection.callAllCallbacks(HandlerType.disconnection)

    def closeClient(self):
        """Force close the connection. Called by the sigint handler. 

        """
        self.socket.__del__()
