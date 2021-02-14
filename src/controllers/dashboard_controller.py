import logging
from threading import Thread

from clients.dashboard_client import DashboardClient
from flask import Flask
from flask_threaded_sockets import Sockets, ThreadedWebsocketServer
from metaclasses.singleton import Singleton
from services.communications import CommunicationService


class DashboardController(metaclass=Singleton):

    app = Flask(__name__)
    sockets = Sockets(app)
    SERVER_PORT = 5000

    @sockets.route('/dashboard')
    def echo_socket(webSocket):
        logging.info('Nouveau client')
        try:
            client = DashboardClient(webSocket)
            CommunicationService.dashboardClients.add(client)
            client.thread.join()
        finally:
            CommunicationService.dashboardClients.remove(client)

    @app.route('/')
    def hello():
        return 'Dashboard Controller'

    def launchServer(self):
        webSocketServer = ThreadedWebsocketServer(
            'localhost',
            DashboardController.SERVER_PORT,
            DashboardController.app
        )
        webSocketServer.serve_forever()

    def launch(self) -> Thread:
        thread = Thread(target=self.launchServer)
        thread.start()
        return thread
