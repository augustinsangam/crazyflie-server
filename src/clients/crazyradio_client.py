
import logging
import time
from multiprocessing.context import Process
from threading import Thread
from typing import List

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.log import LogConfig
from models.client import Client
from models.drone import Drone
from models.message import Message
from utils.timestamp import getTimestamp

logging.basicConfig(level=logging.INFO)


class CrazyflieLogging:
    """
    Simple logging example class that logs the Stabilizer from a supplied
    link uri and disconnects after 5s.
    """

    def __init__(self, link_uri):
        """ Initialize and run the example with the specified link_uri """
        self._cf = Crazyflie(rw_cache='./cache')

        # Connect some callbacks from the Crazyflie API
        self._cf.connected.add_callback(self._connected)
        self._cf.disconnected.add_callback(self._disconnected)
        self._cf.connection_failed.add_callback(self._connection_failed)
        self._cf.connection_lost.add_callback(self._connection_lost)

        logging.info('Connecting to %s' % link_uri)

        # Try to connect to the Crazyflie
        self._cf.open_link(link_uri)

        # Variable used to keep main loop occupied until disconnect
        self.is_connected = True

    def _connected(self, link_uri):
        """ This callback is called form the Crazyflie API when a Crazyflie
        has been connected and the TOCs have been downloaded."""
        print('Connected to %s' % link_uri)

        # The definition of the logconfig can be made before connecting
        self._lg_stab = LogConfig(name='Stabilizer', period_in_ms=500)
        self._lg_stab.add_variable('stabilizer.roll', 'float')
        self._lg_stab.add_variable('stabilizer.pitch', 'float')
        self._lg_stab.add_variable('stabilizer.yaw', 'float')

        # The definition of the logconfig can be made before connecting
        self._lg_battery = LogConfig(name='Battery', period_in_ms=500)
        self._lg_battery.add_variable('pm.vbat', 'float')
        self._lg_battery.add_variable('pm.batteryLevel', 'uint8_t')
        self._lg_battery.add_variable('pm.state', 'int8_t')

        # Adding the configuration cannot be done until a Crazyflie is
        # connected, since we need to check that the variables we
        # would like to log are in the TOC.
        try:
            self._cf.log.add_config(self._lg_stab)
            self._cf.log.add_config(self._lg_battery)
            # This callback will receive the data
            self._lg_stab.data_received_cb.add_callback(self._stab_log_data)
            self._lg_battery.data_received_cb.add_callback(self._stab_log_data)
            # This callback will be called on errors
            self._lg_stab.error_cb.add_callback(self._stab_log_error)
            self._lg_battery.error_cb.add_callback(self._stab_log_error)
            # Start the logging
            self._lg_stab.start()
            self._lg_battery.start()
        except KeyError as e:
            print('Could not start log configuration,'
                  '{} not found in TOC'.format(str(e)))
        except AttributeError:
            print('Could not add Stabilizer log config, bad configuration.')

    def _stab_log_error(self, logconf, msg):
        """Callback from the log API when an error occurs"""
        logging.error('Error when logging %s: %s' % (logconf.name, msg))

    def _stab_log_data(self, timestamp, data, logconf):
        """Callback from a the log API when data arrives"""
        print('[%d][%s]: %s' % (timestamp, logconf.name, data))

    def _connection_failed(self, link_uri, msg):
        """Callback when connection initial connection fails (i.e no Crazyflie
        at the specified address)"""
        logging.error('Connection to %s failed: %s' % (link_uri, msg))
        self.is_connected = False

    def _connection_lost(self, link_uri, msg):
        """Callback when disconnected after a connection has been made (i.e
        Crazyflie moves out of range)"""
        logging.error('Connection to %s lost: %s' % (link_uri, msg))

    def _disconnected(self, link_uri):
        """Callback when the Crazyflie is disconnected (called in all cases)"""
        logging.error('Disconnected from %s' % link_uri)
        self.is_connected = False


class CrazyradioClient(Client):

    def __init__(self, interface: List[str]) -> None:
        self.uri = interface[0]
        drone: Drone = {
            "name": self.uri,
            "speed": 0.0,
            "battery": 0.0,
            "position": [0.0, 0.0, 0.0],
            "timestamp": getTimestamp(),
            "flying": False,
            "ledOn": True
        }
        self.drone = drone
        self.crazyflieLogging = CrazyflieLogging(self.uri)
        self.thread = Thread(
            target=self.handleLogging,
        )
        self.thread.start()

    def handleLogging(self):
        while self.crazyflieLogging.is_connected:
            time.sleep(1)

    def sendMessage(self, message: Message) -> None:
        # messageStr = json.dumps(message)
        # self.socket.send(messageStr)
        pass
