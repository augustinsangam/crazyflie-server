

class Sender():
    __instance = None  # The singleton

    def __new__(cls, dashboardHandlers, robotHandlers):
        if Sender.__instance is None:
            Sender.__instance = object.__new__(cls)
            Sender.__instance.dashboardHandlers = dashboardHandlers
            Sender.__instance.robotHandlers = robotHandlers
        return Sender.__instance

    def sendFromRobotToHandler(self, message):
        for handler in self.__instance.dashboardHandlers:
            handler.sendMessage(message)

    def sendFromDashboardToRobots(self, message):
        for robotHandler in self.__instance.robotHandlers:
            robotHandler.sendMessage(message)
