
import logging
import struct
from typing import List

from cflib.crazyflie import Crazyflie
from models.drone import Drone
from models.message import Message
from services.communications import CommunicationService
from services.drones import DronesService
from utils.timestamp import getTimestamp


class CrazyradioClient:

    def __init__(self, interface: List[str]) -> None:
        self.uri = interface[0]
        drone: Drone = {
            "name": self.uri,
            "speed": 0.0,
            "battery": 0.0,
            "position": [0.0, 0.0, 0.0],
            "timestamp": getTimestamp(),
            "flying": False,
            "ledOn": True,
            "real": False
        }
        self.drone = drone
        self._setupAppChannel()

    def _setupAppChannel(self) -> None:
        self._cf = Crazyflie()
        self._cf.connected.add_callback(self._connected)
        self._cf.disconnected.add_callback(self._disconnected)
        self._cf.connection_failed.add_callback(self._connection_failed)
        self._cf.connection_lost.add_callback(self._connection_lost)
        self._cf.appchannel.packet_received.add_callback(
            self._app_packet_received)
        self._cf.open_link(self.uri)

    def _connected(self, uri):
        """ This callback is called form the Crazyflie API when a Crazyflie
        has been connected and the TOCs have been downloaded."""
        # Start a separate thread to do the motor test.
        # Do not hijack the calling thread!
        logging.info(f"Successfully connected to drone at {uri}")

    def _connection_failed(self, uri, msg):
        """Callback when connection initial connection fails (i.e no Crazyflie
        at the specified address)"""
        logging.error('Connection to %s failed: %s' % (uri, msg))

    def _connection_lost(self, uri, msg):
        """Callback when disconnected after a connection has been made (i.e
        Crazyflie moves out of range)"""
        logging.error('Connection to %s lost: %s' % (uri, msg))

    def _disconnected(self, uri):
        """Callback when the Crazyflie is disconnected (called in all cases)"""
        logging.info('Disconnected from %s' % uri)

    def _app_packet_received(self, data):
        data = struct.unpack("<Qfffff??", data)
        self.drone['timestamp'] = data[0]
        self.drone['speed'] = data[1]
        self.drone['battery'] = data[2]
        self.drone['position'] = [data[3], data[4], data[5]]
        self.drone['flying'] = data[6]
        self.drone['ledOn'] = data[7]
        self.drone['real'] = True
        DronesService.setDrone(self.drone)
        CommunicationService.sendToDashboardClients({
            "type": "pulse",
            "data": self.drone
        })

    def sendMessage(self, message: Message) -> None:
        if message['data']['name'] == self.drone['name'] or message['data']['name'] == '*':
            if message['type'] == 'lighten':
                self._cf.appchannel.send_packet(struct.pack("<?", True))
            elif message['type'] == 'darken':
                self._cf.appchannel.send_packet(struct.pack("<?", False))
            else:
                logging.error(f'Unrecognized command {message}')
