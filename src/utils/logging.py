import logging


def setupLogging() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] %(levelname)s - %(module)s %(funcName)s (%(filename)s:%(lineno)d) - %(message)s',
        datefmt='%H:%M:%S'
    )
