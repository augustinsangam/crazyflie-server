from typing import List, Optional

from src.metaclasses.singleton import Singleton
from src.models.drone import Drone
from src.models.message import Message
from src.models.mission import Mission


class CommunicationService(metaclass=Singleton):

    def __init__(self):
        """Initialize the communication service. The controllers are set to
        None because their object do not exists yet.
        """
        self.dashboardController = None
        self.argosController = None
        self.crazyradioController = None

    def registerControllers(self, dashboard, argos, crazyradio) -> None:
        """Register the controller to the specified values.

          @param dashboard: the object of the dashboard controller.
          @param argos: the object of the argos controller.
          @param crazyradio: the object of the crazyradio controller.
        """
        self.dashboardController = dashboard
        self.argosController = argos
        self.crazyradioController = crazyradio

    def sendToDashboardController(self, message: Message):
        """Send the message to the dashboard controller.
          @param message: the message to send.
        """
        self.dashboardController.onControllerReceivedMessage(message)

    def sendToArgosController(self, message: Message):
        """Send the message to the argos controller.
          @param message: the message to send.
        """
        self.argosController.onControllerReceivedMessage(message)

    def sendToCrazyradioController(self, message: Message):
        """Send the message to the crazyradio controller.
          @param message: the message to send.
        """
        self.crazyradioController.onControllerReceivedMessage(message)

    def getAllDrones(self) -> List[Drone]:
        """Get all the drone saved across the argos and crazyradio controller.
        """
        return list(self.argosController.dronesSet.getDrones().values()) +\
            list(self.crazyradioController.dronesSet.getDrones().values())

    def getCurrentMission(self) -> Optional[Mission]:
        """Returns the current active mission.

        """
        argosMission = self.argosController.getCurrentMission()
        if argosMission is not None:
            return argosMission
        return self.crazyradioController.getCurrentMission()
