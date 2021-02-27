#!/usr/bin/env python3

import logging
import signal

from controllers.argos_controller import ArgosController
from controllers.crazyradio_controller import CrazyradioController
from controllers.dashboard_controller import DashboardController
from services.communications import CommunicationService
from utils.logging import setupLogging


def exitHandler(signal, frame):
    logging.info('Closing server application')
    CrazyradioController.stopServer()
    ArgosController.stopServer()
    DashboardController.stopServer()


if __name__ == '__main__':

    # Some initializations
    setupLogging()

    # Handle terminations
    signal.signal(signal.SIGINT, exitHandler)
    # signal.signal(signal.SIGTERM, exitHandler)
    # signal.signal(signal.SIGHUP, exitHandler)

    # Register all controllers
    CommunicationService().registerControllers(
        DashboardController,
        ArgosController,
        CrazyradioController
    )

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
