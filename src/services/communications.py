from typing import Set

from models.client import Client
from models.message import Message


class CommunicationService:

    dashboardClients: Set[Client] = set()
    argosClients: Set[Client] = set()
    crazyRadioClients: Set[Client] = set()

    @staticmethod
    def sendToDashboardClients(message: Message):
        for client in CommunicationService.dashboardClients:
            client.sendMessage(message)

    @staticmethod
    def sendToArgosClients(message: Message):
        for client in CommunicationService.argosClients:
            client.sendMessage(message)

    @staticmethod
    def sendToAllCrazyradioClients(message: Message):
        for client in CommunicationService.crazyRadioClients:
            client.sendMessage(message)
