#!/usr/bin/env python3

import logging
from multiprocessing import Process
from multiprocessing.context import ProcessError

from clients.dashboard_client import DashboardClient
from flask import Flask
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from metaclasses.singleton import Singleton
from services.communications import CommunicationService


class DashboardController(metaclass=Singleton):

    app = Flask(__name__)
    sockets = Sockets(app)
    SERVER_PORT = 5000

    @sockets.route('/dashboard')
    def echo_socket(webSocket):
        logging.info('Nouveau client')
        client = DashboardClient(webSocket)
        CommunicationService.dashboardClients.add(client)
        client.thread.join()
        CommunicationService.dashboardClients.remove(client)

    @app.route('/')
    def hello():
        return 'Dashboard Controller'

    def launchServer(self):
        webSocketServer = pywsgi.WSGIServer(
            ('', DashboardController.SERVER_PORT),
            DashboardController.app,
            handler_class=WebSocketHandler
        )
        webSocketServer.serve_forever()

    def launch(self) -> Process:
        process = Process(target=self.launchServer)
        process.start()
        return process