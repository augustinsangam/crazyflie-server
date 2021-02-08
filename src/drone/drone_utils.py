"""
robot-handler.py
Singleton class to manage robots and their states
"""

import time
from typing import Dict, TypedDict, Union

from gevent import monkey

monkey.patch_all()


class Drone(TypedDict):
    name: str
    speed: float
    battery: int
    position: dict
    timestamp: int
    isOn: bool


class DroneUtils(object):

    __instance = None  # The singleton

    def __new__(cls):
        if DroneUtils.__instance is None:
            DroneUtils.__instance = object.__new__(cls)
            drones: Dict[str, Drone] = {
                "robot_0": {
                    "name": "drone_0",
                    "speed": 2.8,
                    "battery": 58,
                    "position": [10, 12, 3],
                    "timestamp": int(time.time()),
                    "isOn": True
                }
            }
            DroneUtils.__instance.drones = drones
        return DroneUtils.__instance

    def getDrones(self) -> dict:
        return self.__instance.drones

    def setDrones(self, drones: dict) -> None:
        self.__instance.drones = drones

    def getDrone(self, droneName: str) -> Union[None, Drone]:
        if droneName in self.__instance.drones:
            return self.__instance.drones[droneName]
        return None

    def setDrone(self, drone: Drone) -> None:
        self.__instance.drones[drone['name']] = drone
