import logging
import os
from datetime import datetime

CRITICAL = logging.CRITICAL
FATAL = logging.CRITICAL
ERROR = logging.ERROR
WARNING = logging.WARNING
WARN = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG
NOTSET = logging.NOTSET

_LOGGERS = {}

logger_level = DEBUG

logs_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../log')

if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)


def get_logger(name, level=logger_level, log_file=os.path.join(logs_dir, '%s.log' % str(datetime.utcnow().date()))):
    global _LOGGERS
    if name in _LOGGERS:
        return _LOGGERS[name]
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # add stream handle
    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    # add file logger handle if exist file path
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    _LOGGERS[name] = logger
    return logger


def get_unicode(text):
    if isinstance(text, unicode):
        return text
    return unicode(text, encoding='utf-8', errors='ignore')
