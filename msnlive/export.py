#! /usr/bin/env python
#coding=utf-8
from datetime import datetime
import traceback
from store.appengine import Store

def export():
    db = Store(None)
    filename = '%s.txt' % datetime.today().strftime('%y%m%d')
    db.export(filename)


if __name__ == '__main__':
    export()