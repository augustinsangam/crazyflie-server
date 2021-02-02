"""
robot-handler.py
Singleton class to manage robots and their states
"""

import time
from typing import Dict, Union

from gevent import monkey

from robots.robot import Robot

monkey.patch_all()


class RobotUtils(object):

    __instance = None  # The singleton

    def __new__(cls):
        if RobotUtils.__instance is None:
            RobotUtils.__instance = object.__new__(cls)
            robots: Dict[str, Robot] = {
                "robot_0": {
                    "name": "robot_0",
                    "speed": 2.8,
                    "battery": 58,
                    "position": [10, 12, 3],
                    "timestamp": int(time.time()),
                    "isOn": True
                }
            }
            RobotUtils.__instance.robots = robots
        return RobotUtils.__instance

    def getRobots(self) -> dict:
        return self.__instance.robots

    def setRobots(self, robots: dict) -> None:
        self.__instance.robots = robots

    def getRobot(self, robotName: str) -> Union[None, Robot]:
        if robotName in self.__instance.robots:
            return self.__instance.robots[robotName]
        return None

    def setRobot(self, robot: Robot) -> None:
        self.__instance.robots[robot['name']] = robot
