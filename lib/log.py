import datetime
import json
import logging
import logging.handlers

loggers = {}
log = logging.getLogger()

def log_init(name, level=logging.DEBUG, **kwargs):
    formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s %(message)s')

    if name.endswith('.log'):
        hdlr = logging.handlers.TimedRotatingFileHandler(
            name,
            when=kwargs.get('frequency', 'midnight'),
            interval=kwargs.get('interval', 1),
            backupCount=kwargs.get('backups', 5)
            )
        hdlr.setFormatter(formatter)
        hdlr.setLevel(level)

    if name == "console":
        hdlr = logging.StreamHandler()
        hdlr.setFormatter(formatter)
        hdlr.setLevel(level)
       
    loggers[name] = hdlr
    log.addHandler(hdlr)
    log.setLevel(level)

    return log
