#!/usr/bin/python
#coding=utf8
from pycomm.log import getLogger, cur_log
from logging.handlers import RotatingFileHandler

FORMAT = "<%(levelname)s> <%(name)s> <%(process)d:%(threadName)s>%(asctime)-8s] %(message)s"
fmt = logging.Formatter(format, '%Y-%m-%d_%H:%M:%S')


handler = RotatingFileHandler('/dev/shm/log', maxBytes=50 * 1024 * 1024 , backupCount=4)
handler.setFormatter(fmt)    

log = getLogger(cur_log.name)
log.setLevel(cur_log.level)

