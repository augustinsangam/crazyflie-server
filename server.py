#!/usr/bin/env python3

from dashboard.dashboard_hadler import DashboadHandler
from flask import Flask
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler


app = Flask(__name__)
sockets = Sockets(app)


@sockets.route('/echo')
def echo_socket(ws):
    dashboardHadler = DashboadHandler(ws)  

@app.route('/')
def hello():
    return 'Hello World!'


if __name__ == "__main__":
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()

