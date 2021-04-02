"""dronesSet
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
        """Return a deep copy of the drones.
        """
        return copy(self.__drones)

    def getDrone(self, key: Any) -> Union[None, Drone]:
        """Return the drone identified by the given key.
          @param key: the key witch identifies the drone.
        """
        if key in self.__drones:
            return self.__drones[key]
        return None

    def findDroneByName(self, name: str) -> Union[None, DroneSearchReturn]:
        """Search the saved drone with the given name. Return None if it
        doesn't find any match.

          @param name: the str name of the searched drone.
        """
        key: Any
        drone: Drone
        for key, drone in self.__drones.items():
            if drone['name'] == name:
                return DroneSearchReturn(key=key, drone=drone)
        return None

    def setDrone(self, key: Any, drone: Drone) -> None:
        """Add the given drone to the saved drones.

        @param key: the key witch identifies the drone.
        @param drone: the drone data to save.
        """
        self.__drones[key] = drone

    def removeDrone(self, key: Any) -> None:
        """Revome the drone associatede with the given key.
          @param key: the key that identifies the drone to remove.
        """
        if key in self.__drones:
            del self.__drones[key]
