FROM python:3.8

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y \
	libusb-1.0.0

WORKDIR /opt/cfloader
RUN curl -JR --remote-name-all \
	https://raw.githubusercontent.com/bitcraze/crazyflie-clients-python/master/src/cfloader/__init__.py \
	https://raw.githubusercontent.com/bitcraze/crazyflie-clients-python/master/src/cfloader/__main__.py

WORKDIR /build
ENV PYTHONPATH=/opt

CMD pip -q install -r /server/requirements.txt && python /server/src/server.py
