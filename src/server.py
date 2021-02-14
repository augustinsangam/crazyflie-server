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
    crazyradioControllerThread = CrazyradioController().launch()
    logging.info('Crazyradio controller launched')

    # Argos Controller
    argosControllerThread = ArgosController().launch()
    logging.info('Argos controller launched')

    # Dashboard Controller
    dashboardControllerThread = DashboardController().launch()
    logging.info('Dashboard controller launched')

    # Wait for the Thread to finish
    crazyradioControllerThread.join()
    argosControllerThread.join()
    dashboardControllerThread.join()
    logging.info('All Controllers have stopped')
