#!/usr/bin/env python3

import threading

from clients.dashboard import DashboardClient
from flask import Flask
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from metaclasses.singleton import Singleton
from services.communications import CommunicationService
from utils.logger import Logger


class DashboardController(metaclass=Singleton):

    app = Flask(__name__)
    sockets = Sockets(app)
    SERVER_PORT = 5000

    @sockets.route('/dashboard')
    def echo_socket(webSocket):
        print('Nouveau client')
        client = DashboardClient(webSocket)
        CommunicationService.dashboardClients.add(client)
        client.thread.join()
        CommunicationService.dashboardClients.remove(client)

    @app.route('/')
    def hello():
        return 'Dashboard Controller'

    def launch(self):
        webSocketServer = pywsgi.WSGIServer(
            ('', DashboardController.SERVER_PORT),
            DashboardController.app,
            handler_class=WebSocketHandler
        )
        webSocketServer.serve_forever()
