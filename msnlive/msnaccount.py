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

class MSNAccountDB(MSNCIDSDB):
    TARGET_BASE = 'cache_sender'
    EXPORT_LIMIT = 200000 
    def __init__(self, dbfile="/Users/ttwait/work/data/leveldb/msnaccount.ldb"):
        MSNCIDSDB.__init__(self, dbfile)
        
        
def main():
    app = MSNAccountDB()
    app.run()

if __name__ == '__main__':
    main()
    
