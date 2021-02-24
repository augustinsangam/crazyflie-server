FROM ubuntu:20.04

RUN apt-get update && apt-get install -y build-essential git python-dev python3 python3-pip make gcc-arm-none-eabi usbutils apt-utils

RUN git clone https://github.com/bitcraze/crazyflie-lib-python
RUN cd crazyflie-lib-python && pip3 install -r requirements.txt

RUN usermod -a -G plugdev root

RUN apt-get install -y udev

RUN mkdir -p /etc/udev/rules.d/ && touch /etc/udev/rules.d/99-crazyradio.rules
RUN echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="1915", ATTRS{idProduct}=="7777", MODE="0664", GROUP="plugdev"' >> /etc/udev/rules.d/99-crazyradio.rules
RUN echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="1915", ATTRS{idProduct}=="0101", MODE="0664", GROUP="plugdev"' >> /etc/udev/rules.d/99-crazyradio.rules

# RUN udevadm control --reload-rules
# RUN udevadm trigger

RUN git clone  https://github.com/bitcraze/crazyflie-firmware.git --recursive
WORKDIR /crazyflie-firmware/examples/app_hello_world
COPY ./src/basic-firmwares/pdr.c ./src/hello_world.c
RUN make -j $(nproc)

RUN ls

WORKDIR /code
COPY ./src .
# Copy the requirements file
COPY requirements.txt ./
# Install the requirements
RUN apt install -y python3-venv
RUN pip3 install --no-cache-dir -r requirements.txt
# Create environment
RUN python3 -m venv .venv
# Activate the environment
RUN . ./.venv/bin/activate
# Install wheel and uwsgi package
RUN pip3 install wheel uwsgi
#CMD [ "uwsgi", "--ini=wsgi.ini" ]

# SETUP USB HERE
RUN groups
RUN lsusb

COPY cfloader cfloader
#CMD udevadm control --reload-rules && udevadm trigger && python3 ./server.py
ENV CF2_BIN=/crazyflie-firmware/examples/app_hello_world/cf2.bin
#ENV PYUSB_DEBUG=debug
CMD [ "python3", "./server.py" ]
