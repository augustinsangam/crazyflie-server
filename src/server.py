#!/usr/bin/env python3

from gevent import monkey

from controllers.argos import ArgosController
from controllers.dashboard import DashboardController
from utils.logger import Logger


def exitHandler(signal, frame):
    print('CLOSINGGGGGGGGGG')
    pass


if __name__ == '__main__':
    monkey.patch_all()
    # signal.signal(signal.SIGINT, exitHandler)
    # signal.signal(signal.SIGTERM, exitHandler)
    # signal.signal(signal.SIGHUP, exitHandler)
    logger = Logger()
    logger.log('Launching argos controller')
    ArgosController().launch()
    logger.log('Launching dashboard controller')
    # This last one blocks
    DashboardController().launch()
