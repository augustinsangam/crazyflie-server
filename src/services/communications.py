from typing import List

from src.metaclasses.singleton import Singleton
from src.models.drone import Drone
from src.models.message import Message


class CommunicationService(metaclass=Singleton):

    def __init__(self):
        self.dashboardController = None
        self.argosController = None
        self.crazyradioController = None

    def registerControllers(self, dashboard, argos, crazyradio) -> None:
        self.dashboardController = dashboard
        self.argosController = argos
        self.crazyradioController = crazyradio

    def sendToDashboardController(self, message: Message):
        self.dashboardController.sendMessage(message)

    def sendToArgosController(self, message: Message):
        self.argosController.sendMessage(message)

    def sendToCrazyradioController(self, message: Message):
        self.crazyradioController.sendMessage(message)

    def getAllDrones(self) -> List[Drone]:
        return list(self.argosController.dronesSet.getDrones().values()) +\
            list(self.crazyradioController.dronesSet.getDrones().values())
