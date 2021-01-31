#!/usr/bin/env python3

from flask import Flask
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from dashboard.dashboard_handler import DashboardHandler

app = Flask(__name__)
sockets = Sockets(app)


@sockets.route('/dashboard')
def echo_socket(ws):
    dashboardHandler = DashboardHandler(ws)  

@app.route('/')
def hello():
    return 'Hello World!'


if __name__ == "__main__":
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()

