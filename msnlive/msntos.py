#! /usr/bin/env python
#coding=utf-8
from msncidsdb import MSNCIDSDB
from optparse import OptionParser
import leveldb
import sys
import os
import os.path as osp
import logging
from pycomm.log import log, open_log, open_debug

class MSNTosDB(MSNCIDSDB):
    TARGET_BASE = 'tos'
    EXPORT_LIMIT = 1000000 
    def __init__(self, dbfile="dumps/tosdata.lds"):
        MSNCIDSDB.__init__(self, dbfile)
        
        
def main():
    app = MSNTosDB()
    app.run()

if __name__ == '__main__':
    main()
    
