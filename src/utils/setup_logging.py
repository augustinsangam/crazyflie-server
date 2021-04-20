import logging

import coloredlogs
from src.models.message import Message
from src.models.software_update import LoadProjectLog, LogType
from src.services.communications import CommunicationService

SUCCESS_LEVEL_NUM = 25


class DashboardLogger(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        logEntry = self.format(record)
        CommunicationService().sendToDashboardController(
            Message(
                type='loadProjectLog',
                data=LoadProjectLog(
                    log=logEntry,
                    type=DashboardLogger.getDashBoardLevelName(record),
                    timestamp=int(record.created)
                )
            )
        )

    @staticmethod
    def getDashBoardLevelName(record: logging.LogRecord) -> LogType:
        if record.levelno in [logging.ERROR, logging.CRITICAL]:
            return 'error'
        if record.levelno == logging.WARNING:
            return 'warning'
        if record.levelno == logging.INFO:
            return 'info'
        return 'success'


def setupLogging() -> None:
    """Set the format of the logging tool.
    """

    fmt = '[%(asctime)s] %(levelname)s - (%(filename)s:%(lineno)d) - %(' \
          'message)s '

    coloredlogs.install(level=logging.INFO, fmt=fmt)

    logging.addLevelName(SUCCESS_LEVEL_NUM, 'SUCCESS')

    logging.getLogger('cflib.crtp').setLevel(logging.ERROR)
    logging.getLogger('flib.drivers.cfusb').setLevel(logging.ERROR)
    logging.getLogger('cflib.crazyflie').setLevel(logging.ERROR)
    logging.getLogger(
        'cflib.crazyflie.platformservice').setLevel(logging.ERROR)
    logging.getLogger('cflib.crazyflie.toccache').setLevel(logging.ERROR)
    logging.getLogger('cflib.crazyflie.mem').setLevel(logging.ERROR)
    logging.getLogger('cflib.drivers.cfusb').setLevel(logging.ERROR)

    rootLogger = logging.getLogger()
    formatter = logging.Formatter(fmt=fmt)
    rootLogger.addHandler(logging.FileHandler('debug.log'))
    rootLogger.addHandler(DashboardLogger())
    for handler in rootLogger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.setFormatter(formatter)
