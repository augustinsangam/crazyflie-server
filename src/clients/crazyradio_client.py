from typing import Union

from cflib.crazyflie import Crazyflie
from src.models.connection import Connection, HandlerType


class CrazyradioClient:

    def __init__(self) -> None:
        self.uri = ''
        self._cf: Union[Crazyflie, None] = None
        self.connection = Connection()

    def connect(self, droneUri: str) -> None:
        self.uri = droneUri
        self._cf = Crazyflie()

        self._cf.connected.add_callback(
            lambda uri: self.connection.callAllCallbacks(HandlerType.connection))

        self._cf.disconnected.add_callback(
            lambda uri: self.connection.callAllCallbacks(HandlerType.disconnection))

        self._cf.connection_failed.add_callback(
            lambda uri, msg: self.connection.callAllCallbacks(HandlerType.error, msg))

        self._cf.connection_lost.add_callback(
            lambda uri, msg: self.connection.callAllCallbacks(HandlerType.error, msg))

        self._cf.appchannel.packet_received.add_callback(
            lambda uri, data: self.connection.callAllCallbacks(HandlerType.error, data))

        self._cf.open_link(droneUri)

    def sendMessage(self, message: str) -> None:
        self._cf.appchannel.send_packet(bytes(message, 'ascii'))

    def closeClient(self) -> None:
        self._cf.close_link()
