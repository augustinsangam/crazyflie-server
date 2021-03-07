#!/usr/bin/env python3

import logging
import pathlib
import signal
import sys
from models.mission import MissionPulse

# Launch server in server/ folder
sys.path.insert(
    0, 
    pathlib.Path(__file__).parent.parent.absolute().__str__()
)

# Now imports works
from src.controllers.argos_controller import ArgosController
from src.controllers.crazyradio_controller import CrazyradioController
from src.controllers.dashboard_controller import DashboardController
from src.services.communications import CommunicationService
from src.utils.setup_logging import setupLogging
from services.database import DatabaseService

def exitHandler(sig, frame):
    logging.info('Closing server application')
    CrazyradioController.stopServer()
    ArgosController.stopServer()
    DashboardController.stopServer()


if __name__ == '__main__':

    # Some initializations
    setupLogging()

    # Handle terminations
    signal.signal(signal.SIGINT, exitHandler)
    signal.signal(signal.SIGTERM, exitHandler)
    signal.signal(signal.SIGHUP, exitHandler)

    # Register all controllers
    CommunicationService().registerControllers(
        DashboardController,
        ArgosController,
        CrazyradioController
    )

    # Terminate any in progress missions
    missions = DatabaseService.getAllMissions()
    
    for mission in missions:
        if mission['status'] == 'inProgress':
            missionPulse = MissionPulse(
                id=mission['id'],
                status='failed'
            )
            DatabaseService.saveMission(missionPulse['id'], missionPulse)

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
