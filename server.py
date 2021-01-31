#!/usr/bin/env python3

import socket
import threading
from typing import Set

from flask import Flask
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from dashboard.dashboard_handler import DashboardHandler

app = Flask(__name__)
sockets = Sockets(app)

dashboardHandlers = set()

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

        conn, addr = server.accept()

        print('Connection address:', addr)

        client_handler = threading.Thread(
            target=handle_client_connection,
            args=(conn,)
        )
        client_handler.start()


def handle_client_connection(client_socket):
    while True:
        print('wait for reception')
        request = client_socket.recv(1024)
        print(f'Received {request}')
        client_socket.send(bytes('ACK!', 'ascii'))
        print('ACK sent')


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
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    t = threading.Thread(target=launchServer)
    t.daemon = True
    t.start()
    server.serve_forever()
