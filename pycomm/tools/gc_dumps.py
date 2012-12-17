#! /usr/bin/env python
#coding=utf-8
import gc
import cPickle as pickle
import datetime
import os
import time

normal_obj = {}

def get_normal_obj():
    gc.collect()
    objs = gc.get_objects()
    for item in objs:
        normal_obj[id(item)] = True

get_normal_obj()

def dump(path):
    if not os.path.exists(path):
        os.makedirs(path)
    f = file('%s/%s_%s.pl' % (path, os.getpid(), datetime.datetime.now().strftime('%y%m%d%H%M%S')), 'w')
    gc.collect()
    objs = gc.get_objects()
    print >>f, len(objs)
    for item in objs:
        if id(item) in normal_obj or item == normal_obj:
            continue
        print >> f, item
        print >>f, '\n\n\n'
    f.close()

last_dump_time = 0
def auto_dump(interval=60, path='/home/qspace/data/gc'):
    global last_dump_time
    if (last_dump_time + interval) > time.time():
        return
    
    dump(path)
    last_dump_time = time.time()
