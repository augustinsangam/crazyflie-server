#!/usr/bin/env python3

import logging

from controllers.argos_controller import ArgosController
from controllers.crazyradio_controller import CrazyradioController
from controllers.dashboard_controller import DashboardController
from utils.logging import setupLogging


def exitHandler(signal, frame):
    logging.info('CLOSING SERVER APPLICATION')
    pass


if __name__ == '__main__':

    # Some initializations
    setupLogging()

    # Handle terminations
    # signal.signal(signal.SIGINT, exitHandler)
    # signal.signal(signal.SIGTERM, exitHandler)
    # signal.signal(signal.SIGHUP, exitHandler)

    # Crazyradio Controller
    crazyradioControllerProcess = CrazyradioController().launch()
    logging.info('Crazyradio controller launched')

    # Argos Controller
    argosControllerProcess = ArgosController().launch()
    logging.info('Argos controller launched')

    # Dashboard Controller
    dashboardControllerProcess = DashboardController().launch()
    logging.info('Dashboard controller launched')

    # Wait for the process to finish
    crazyradioControllerProcess.join()
    # argosControllerProcess.join()
    # dashboardControllerProcess.join()
    logging.info('All Controllers have stopped')
