"""
robot-handler.py
Singleton class to manage robots and their states
"""

import time
from typing import Dict, Union

from models.drone import Drone


class DronesService:

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

    @staticmethod
    def getDrones() -> dict:
        return DronesService.drones

    @staticmethod
    def setDrones(drones: dict) -> None:
        DronesService.drones = drones

    @staticmethod
    def getDrone(droneName: str) -> Union[None, Drone]:
        if droneName in DronesService.drones:
            return DronesService.drones[droneName]
        return None

    @staticmethod
    def setDrone(drone: Drone) -> None:
        DronesService.drones[drone['name']] = drone
