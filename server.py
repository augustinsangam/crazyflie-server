#!/usr/bin/env python3

import socket
import threading
from typing import Set

from flask import Flask
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from utils import Sender
from dashboard.dashboard_handler import DashboardHandler
from robots.robot_communication_handler import RobotCommunicationHandler

import socket
import threading


app = Flask(__name__)
sockets = Sockets(app)

dashboardHandlers = set()
robotHandlers = set()

TCP_IP = '127.0.0.1'
TCP_PORT = 3995
BUFFER_SIZE = 20


def launchServer():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((TCP_IP, TCP_PORT))
    server.listen(2)

    print('waiting for connection')
    while True:

        clientSocket, addr = server.accept()

        print('Connection address:', addr)

        robotHandler = RobotCommunicationHandler(clientSocket)

        robotHandlers.add(robotHandler)


@sockets.route('/dashboard')
def echo_socket(ws):
    handler = DashboardHandler(ws)
    dashboardHandlers.add(handler)
    handler.thread.join()
    print('handler closed')
    dashboardHandlers.remove(handler)


@app.route('/')
def hello():
    return 'Hello World!'


if __name__ == "__main__":
    sender = Sender(dashboardHandlers, robotHandlers)
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    t = threading.Thread(target=launchServer)
    t.daemon = True
    t.start()
    server.serve_forever()
