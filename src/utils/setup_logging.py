import logging

import coloredlogs


def setupLogging() -> None:

    coloredlogs.install(
        level=logging.INFO,
        fmt='[%(asctime)s] %(levelname)s - (%(filename)s:%(lineno)d) - %(message)s'
    )

    logging.getLogger('cflib.crtp').setLevel(logging.ERROR)
    logging.getLogger('flib.drivers.cfusb').setLevel(logging.ERROR)
    logging.getLogger('cflib.crazyflie').setLevel(logging.ERROR)
    logging.getLogger(
        'cflib.crazyflie.platformservice').setLevel(logging.ERROR)
    logging.getLogger('cflib.crazyflie.toccache').setLevel(logging.ERROR)
    logging.getLogger('cflib.crazyflie.mem').setLevel(logging.ERROR)
    logging.getLogger('cflib.drivers.cfusb').setLevel(logging.ERROR)
