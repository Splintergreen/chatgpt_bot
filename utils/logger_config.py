import logging
import os
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

date = datetime.now().strftime('%Y-%m-%d')
log_directory = 'logs'

if not os.path.exists(log_directory):
    os.makedirs(log_directory)

log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(filename)s - %(lineno)d - %(levelname)s - %(message)s'
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
