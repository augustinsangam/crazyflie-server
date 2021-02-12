

class CommunicationService:

    dashboardClients = set()
    argosClients = set()

    @staticmethod
    def sendToDashboardClients(message):
        for client in CommunicationService.dashboardClients:
            client.sendMessage(message)

    @staticmethod
    def sendToArgosClients(message):
        for client in CommunicationService.argosClients:
            client.sendMessage(message)

    # Might not be usefull
    # def dropDashboardHandler(self, dashboardHandler) -> None:
    #     self.dashboardHandlers.remove(dashboardHandler)
    #     print('DashboardHandler closed')

    # def removeDroneCommunicationHandler(self, robotHandler) -> None:
    #     self.droneCommunicationHandlers.remove(robotHandler)
    #     print('Drone communication handler closed')
