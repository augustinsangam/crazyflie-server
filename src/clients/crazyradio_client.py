import json
import logging
import struct

from typing import Union
from io import StringIO

from cflib.crazyflie import Crazyflie
from src.models.connection import Connection, HandlerType
from src.models.message import Message


class CrazyradioClient:

    def __init__(self) -> None:
        self.uri = ''
        self._cf: Union[Crazyflie, None] = None
        self.connection = Connection()

    def connect(self, droneUri: str) -> None:
        """Assign the client to the connection. Add callbacks for the
        different events.

          @param droneUri: the drone's identifier.
        """
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
            lambda data: self.connection.callAllCallbacks(HandlerType.message, data))

        self._cf.open_link(droneUri)

    def sendMessage(self, message: Message) -> None:
        """Take given message string and sends it as bytes to the appchannel.

          @param message: the message to send
        """
        if message['data']['name'] == self.uri or message['data']['name'] == '*':
            if message['type'] == 'lighten':
                self._cf.appchannel.send_packet(struct.pack("<?", True))
            elif message['type'] == 'darken':
                self._cf.appchannel.send_packet(struct.pack("<?", False))
            else:
                logging.error(
                    f'Crazyradio got unrecognized command to send : {message}')

    def closeClient(self) -> None:
        """Force close the client connection. Called by the sigint handler

        """
        self._cf.close_link()
