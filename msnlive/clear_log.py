#! /usr/bin/env python
#coding=utf-8
import os
import os.path as osp
import sys
from datetime import datetime

path = '/root/data/log/'

filename = osp.join('%s.log' % datetime.today().strftime('%m%d%H'))

os.chdir(path)
for f in os.listdir('.'):
    if f != filename:
        os.unlink(f)