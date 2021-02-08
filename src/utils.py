

class Sender():
    __instance = None  # The singleton

    def __new__(cls, dashboardCommunicationHandlers, droneCommunicationHandlers):
        if Sender.__instance is None:
            Sender.__instance = object.__new__(cls)
            Sender.__instance.dashboardCommunicationHandlers = dashboardCommunicationHandlers
            Sender.__instance.droneCommunicationHandlers = droneCommunicationHandlers
        return Sender.__instance

    def sendToDashboards(self, message):
        for dashboardCommunicationHandler in self.__instance.dashboardCommunicationHandlers:
            dashboardCommunicationHandler.sendMessage(message)

    def sendToDrones(self, message):
        for droneCommunicationHandler in self.__instance.droneCommunicationHandlers:
            droneCommunicationHandler.sendMessage(message)

    # Might not be usefull
    # def dropDashboardHandler(self, dashboardHandler) -> None:
    #     self.__instance.dashboardHandlers.remove(dashboardHandler)
    #     print('DashboardHandler closed')

    def removeDroneCommunicationHandler(self, robotHandler) -> None:
        self.__instance.droneCommunicationHandlers.remove(robotHandler)
        print('Drone communication handler closed')
