#!/usr/bin/env python3

import socket
import threading
import signal

from typing import Set
from flask import Flask
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from src.utils import Sender
from src.dashboard.dashboard_communication_handler import DashboardCommunicationHandler
from src.drone.drone_communication_handler import DroneCommunicationHandler


app = Flask(__name__)
sockets = Sockets(app)

dashboardCommunicationHandlers = set()
droneCommunicationHandlers = set()

TCP_IP = '127.0.0.1'
TCP_PORT = 3995
BUFFER_SIZE = 20


def exitHandler(signal, frame):
    for dashboardHandler in dashboardCommunicationHandlers:
        dashboardHandler.socket.close()

    for droneCommunicationHandler in droneCommunicationHandlers:
        droneCommunicationHandler.socket.settimeout(0)

    # webSocketServer.stop()


def launchServer():
    TCPServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    TCPServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    TCPServer.bind((TCP_IP, TCP_PORT))
    TCPServer.listen(2)

    while True:
        clientSocket, addr = TCPServer.accept()
        print('Drone connected')
        droneCommunicationHandler = DroneCommunicationHandler(clientSocket)
        droneCommunicationHandlers.add(droneCommunicationHandler)


@sockets.route('/dashboard')
def echo_socket(webSocker):
    communication = DashboardCommunicationHandler(webSocker)
    dashboardCommunicationHandlers.add(communication)
    communication.thread.join()
    dashboardCommunicationHandlers.remove(communication)


@app.route('/')
def hello():
    return 'Hello World!'


if __name__ == "__main__":
    sender = Sender(dashboardCommunicationHandlers, droneCommunicationHandlers)

    signal.signal(signal.SIGINT, exitHandler)

    webSocketServer = pywsgi.WSGIServer(
        ('', 5000), app, handler_class=WebSocketHandler)

    TCPServer = threading.Thread(target=launchServer)
    TCPServer.daemon = True
    TCPServer.start()

    webSocketServer.serve_forever()

    print('Stopped')
