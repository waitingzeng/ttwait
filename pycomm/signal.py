#! /usr/bin/env python
#coding=utf-8
import signal
import os 
import time
from pycomm.log import log
ALIVE = True 


callbacks = []

def sigint_handler(signum, frame):
    log.trace('handler %u %s', signum, frame)
    global ALIVE
    if callbacks:
        for func in callbacks:
            if callable(func):
                func()
    ALIVE = False
    
try:
    
    signal.signal(signal.SIGINT, sigint_handler) 
  
    if not os.name == 'nt':
        signal.signal(signal.SIGHUP, sigint_handler)
        #signal.signal(signal.SIGKILL, sigint_handler)
  
    signal.signal(signal.SIGTERM, sigint_handler)
except:
    pass
 

if __name__ == '__main__':
    from pycomm.log import open_debug
    open_debug()
    while ALIVE:
        try:
            time.sleep(1)
            print 'aa'
        except:
            pass
