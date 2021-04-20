FROM python:3.8

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
	apt-get install -y \
	libusb-1.0.0

WORKDIR /build

CMD pip -q install -r /server/requirements.txt && python /server/server.py
