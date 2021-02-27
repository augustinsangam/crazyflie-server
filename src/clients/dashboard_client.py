import logging
from threading import Thread

from models.connection import Connection, HandlerType


class DashboardClient:

    def __init__(self) -> None:
        self.connection = Connection()

    def connect(self, socket) -> None:
        self.socket = socket
        self.thread = Thread(target=self.handleCommunications,)
        self.thread.start()

    def handleCommunications(self) -> None:
        self.connection.callAllCallbacks(HandlerType.connection)
        logging.info(f'socket status 1 {self.socket.closed}')
        try:
            while not self.socket.closed:
                logging.info(f'socket status 2 {self.socket.closed}')
                message = self.socket.receive()
                logging.info(f'socket status 3 {self.socket.closed}')
                self.connection.callAllCallbacks(
                    HandlerType.message, message)

        except Exception as e:
            logging.error(e)
            self.socket.close()
            self.connection.callAllCallbacks(HandlerType.error, e)
        finally:
            pass
            self.connection.callAllCallbacks(HandlerType.disconnection)

    def closeClient(self):
        self.socket.__del__()
