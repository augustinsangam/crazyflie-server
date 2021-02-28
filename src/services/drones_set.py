"""
robot-handler.py
Static class to manage robots and their states
"""
from copy import copy
from typing import Any, Dict, TypedDict, Union

from src.models.drone import Drone


class DroneSearchReturn(TypedDict):
    key: Any
    drone: Drone


class DronesSet:

    def __init__(self) -> None:
        drones: Dict[Any, Drone] = {}
        self.__drones = drones

    def getDrones(self) -> dict:
        return copy(self.__drones)

    def getDrone(self, key: Any) -> Union[None, Drone]:
        if key in self.__drones:
            return self.__drones[key]
        return None

    def findDroneByName(self, name: str) -> Union[None, DroneSearchReturn]:
        key: Any
        drone: Drone
        for key, drone in self.__drones.items():
            if drone['name'] == name:
                return DroneSearchReturn(key=key, drone=drone)
        return None

    def setDrone(self, key: Any, drone: Drone) -> None:
        self.__drones[key] = drone

    def removeDrone(self, key: Any) -> None:
        if key in self.__drones:
            del self.__drones[key]
