#!/bin/env python
#coding=utf8
import os
import sys
import datetime
import os.path as osp
from pycomm.log import log, open_log, open_debug
from pycomm.proc.procpool import ProcPool


class Application(ProcPool):
    def init(self):
        self.pjs = self.conf.pjs
        self.logpath = self.conf.logpath
        self.jsname = '%s.js' % osp.splitext(osp.basename(__file__))[0]
        open_debug()


    def work(self, name, id):
        t = datetime.datetime.now()
        newlogfile = "%s/%s.log" % (self.logpath, t.strftime("%m%d%H"))
        #cmd = '%s server.js %s >> %s ' % ( self.pjs, self.id, newlogfile)
        cmd = '%s %s %s ' % ( self.pjs, self.jsname, id)
        log.trace('run cmd `%s`', cmd)
        res = os.system(cmd)






if __name__ == "__main__":
    app = Application()
    app.run()

