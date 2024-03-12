import logging
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime


date = datetime.now().strftime('%Y-%m-%d')
log_directory = 'logs'

if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    handler = TimedRotatingFileHandler(
        f'{log_directory}/log_GPTbot_{date}.log',
        when='midnight',
        interval=1,
        backupCount=10
        )
    handler.setFormatter(log_format)

    logger.addHandler(handler)
    return logger
