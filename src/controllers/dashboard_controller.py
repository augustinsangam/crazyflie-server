import json
import logging
from io import StringIO
from threading import Thread
from typing import List, Set

from flask_threaded_sockets.websocket import WebSocket
from services.database import DatabaseService

from src.clients.dashboard_client import DashboardClient
from flask import Flask
from flask_threaded_sockets import Sockets, ThreadedWebsocketServer
from src.metaclasses.singleton import Singleton
from src.models.connection import HandlerType
from src.models.drone import Drone
from src.models.message import Message
from src.services.communications import CommunicationService


class DashboardController(metaclass=Singleton):
    app = Flask(__name__)
    sockets = Sockets(app)
    HOST = '0.0.0.0'
    SERVER_PORT = 5000
    webSocketServer = None
    clients: Set[DashboardClient] = set()

    @staticmethod
    def launch() -> Thread:
        """Launches a thread in witch the webSocket server will start, and return that thread.

        """
        thread = Thread(target=DashboardController.launchServer)
        thread.start()
        return thread

    @staticmethod
    def launchServer():
        """Start the websocket server.

        """
        webSocketServer = ThreadedWebsocketServer(
            DashboardController.HOST,
            DashboardController.SERVER_PORT,
            DashboardController.app
        )
        DashboardController.webSocketServer = webSocketServer
        webSocketServer.serve_forever()

    @staticmethod
    def stopServer():
        """Closes all the clients connections, then closes the server.

        """
        for client in DashboardController.clients:
            client.closeClient()
        DashboardController.webSocketServer.shutdown()

    @staticmethod
    def handleClient(webSocket: WebSocket):
        """Creates a client witch will listen to the new connection. Callbacks handlers are set for every event.

          @param webSocket: the socket of the new connection.
        """
        client = DashboardClient()
        DashboardController.clients.add(client)
        handlers = [
            [HandlerType.connection, DashboardController.onClientConnect],
            [HandlerType.disconnection, DashboardController.onClientDisconnect],
            [HandlerType.message, DashboardController.onClientReceivedMessage],
            [HandlerType.error, DashboardController.onClientRaisedError],
        ]
        for handlerType, handlerFunc in handlers:
            client.connection.addCallback(
                handlerType,
                handlerFunc,
                client
            )
        client.connect(webSocket)
        client.thread.join()

    @staticmethod
    def onClientConnect(client: DashboardClient) -> None:
        """Called by a client when it connects to its socket.

          @param client: the client witch called the function.
        """
        logging.info(
            f'New Dashboard client connected on socket {client.socket}')
        DashboardController.sendAllRobotsStatus(client.socket)
        DashboardController.sendAllMissions(client.socket)

    @staticmethod
    def onClientDisconnect(client: DashboardClient) -> None:
        """Called by a client when it disconnects from its socket.

          @param client: the client witch called the function.
        """
        logging.info(
            f'Dashboard client disconnected from socket {client.socket}')
        DashboardController.clients.remove(client)

    @staticmethod
    def onClientReceivedMessage(client: DashboardClient, message: str) -> None:
        """Called by a client when it receives a message. The message is parsed as json, \
            then sent to all aof the drones (physical and simulated).

          @param client: the client witch called the function.
          @param message: the message received by the client.
        """
        if message is None:
            return
        try:
            parsedMessage = json.load(StringIO(message))
        except ValueError:
            logging.error(
                f'Dashboard client {client.socket} receive a wrong json format : {message}')
        else:
            logging.info(
                f'Dashboard client {client.socket} received message : {message}')
            CommunicationService().sendToArgosController(parsedMessage)
            CommunicationService().sendToCrazyradioController(parsedMessage)

    @staticmethod
    def onClientRaisedError(client: DashboardClient, error: Exception) -> None:
        """Called when a client raises an error while it waits for messages.

          @param client: the client witch called the function.
          @param error: the exception  raised by the client.
        """
        logging.info(
            f'Dashboard client {client.socket} raised an error:\n{error}')

    @staticmethod
    def sendAllRobotsStatus(socket) -> None:
        """Send all the information of every saved drones to the socket.

          @param socket: the socket to send the info to.
        """
        logging.info(
            'Sending all robots status to new Dashboard client')
        drones: List[Drone] = CommunicationService().getAllDrones()
        for drone in drones:
            DashboardController.sendMessageToSocket(
                socket,
                Message(type="pulse", data=drone)
            )

    def sendAllMissions(socket) -> None:
        logging.info('Sending all saved missions to new Dashboard client')
        missions = DatabaseService.getAllMissions()
        for mission in missions:
            DashboardController.sendMessageToSocket(
                socket,
                Message(type="mission", data=mission)
            )

    @staticmethod
    def sendMessage(message: Message) -> None:
        """Send the specified message to all of the clients.

          @param message: the message to send.
        """
        for client in DashboardController.clients:
            DashboardController.sendMessageToSocket(client.socket, message)

    @staticmethod
    def sendMessageToSocket(socket, message: Message) -> None:
        """Sends the specified message to the specified socket after converting it from json to string.

          @param socket: the socket to send the message.
          @param message: the message to send.
        """
        messageStr = json.dumps(message)
        socket.send(messageStr)


@DashboardController.sockets.route('/dashboard')
def handleNewSocketConnection(webSocket: WebSocket):
    DashboardController.handleClient(webSocket)


@DashboardController.app.route('/')
def handleNewHttpConnection():
    return 'Dashboard Controller'
