import logging

import coloredlogs

coloredlogs.install()


def setupLogging() -> None:
    logging.basicConfig(
        # level=logging.DEBUG,
        level=logging.DEBUG,
        format='[%(asctime)s] %(levelname)s - %(module)s %(funcName)s (%(filename)s:%(lineno)d) - %(message)s',
        datefmt='%H:%M:%S'
    )
    logging.getLogger('cflib.crtp').setLevel(logging.ERROR)
    logging.getLogger('flib.drivers.cfusb').setLevel(logging.ERROR)
    logging.getLogger('cflib.crazyflie').setLevel(logging.ERROR)
    logging.getLogger(
        'cflib.crazyflie.platformservice').setLevel(logging.ERROR)
    logging.getLogger('cflib.crazyflie.toccache').setLevel(logging.ERROR)
    logging.getLogger('cflib.crazyflie.mem').setLevel(logging.ERROR)
    logging.getLogger('cflib.drivers.cfusb').setLevel(logging.ERROR)
