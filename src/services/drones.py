"""
robot-handler.py
Singleton class to manage robots and their states
"""

import time
from typing import Dict, Union

from models.drone import Drone


class DronesService:

    __drones: Dict[str, Drone] = {
        "robot_0": {
            "name": "drone_0",
            "speed": 2.8,
            "battery": 58,
            "position": [10, 12, 3],
            "timestamp": int(time.time()),
            "isOn": True
        }
    }

    @staticmethod
    def getDrones() -> dict:
        return DronesService.__drones

    @staticmethod
    def setDrones(drones: dict) -> None:
        DronesService.__drones = drones

    @staticmethod
    def getDrone(droneName: str) -> Union[None, Drone]:
        if droneName in DronesService.__drones:
            return DronesService.__drones[droneName]
        return None

    @staticmethod
    def setDrone(drone: Drone) -> None:
        DronesService.__drones[drone['name']] = drone