"""
robot-handler.py
Singleton class to manage robots and their states
"""

from typing import Dict, Union

from robots.robot import Robot


class RobotHandler(object):

    __instance = None  # The singleton

    def __new__(cls):
        if RobotHandler.__instance is None:
            RobotHandler.__instance = object.__new__(cls)
        robots: Dict[str, Robot] = {
            "robot1": {
                "name": "robot1",
                "speed": 1.2574998,
                "batteryPercentage": 96,
                "localisation": {"x": 20, "y": 2, "z": 15},
                "lastUpdate": "je sais pas",
                "isOn": True
            },
            "robot2": {
                "name": "robot2",
                "speed": 2.8,
                "batteryPercentage": 58,
                "localisation": {"x": 56, "y": 21, "z": 30},
                "lastUpdate": "je sais pas",
                "isOn": True
            }
        }
        RobotHandler.__instance.robots = robots
        return RobotHandler.__instance

    def getRobots(self) -> dict:
        return self.__instance.robots

    def setRobots(self, robots: dict) -> None:
        self.__instance.robots = robots

    def getRobot(self, robotName: str) -> Union[None, Robot]:
        if robotName in self.__instance.robots:
            return self.__instance.robots[robotName]
        return None

    def setRobot(self, robot: Robot) -> None:
        self.__instance.robots[robot.name] = robot
