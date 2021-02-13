#!/usr/bin/env python3

import logging

from gevent import monkey

from controllers.argos_controller import ArgosController
from controllers.dashboard_controller import DashboardController
from utils.logging import setupLogging


def exitHandler(signal, frame):
    logging.info('CLOSING SERVER APPLICATION')
    pass


if __name__ == '__main__':
    monkey.patch_all()
    setupLogging()
    # signal.signal(signal.SIGINT, exitHandler)
    # signal.signal(signal.SIGTERM, exitHandler)
    # signal.signal(signal.SIGHUP, exitHandler)
    argosControllerProcess = ArgosController().launch()
    logging.info('Argos controller launched')
    dashboardControllerProcess = DashboardController().launch()
    logging.info('Dashboard controller launched')
    argosControllerProcess.join()
    dashboardControllerProcess.join()
    logging.log('All Controllers have stopped')
