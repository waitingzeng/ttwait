#! /usr/bin/env python
#coding=utf-8
from optparse import OptionParser
import leveldb
from pycomm.db.level import LevelDB
import sys
import os
import os.path as osp
import logging
from pycomm.log import log, open_log, open_debug

SYNC = 100000
class MSNCIDSDB(LevelDB):
    TARGET_BASE = 'tos'
    EXPORT_LIMIT = 1000000
    def __init__(self, path="/Users/ttwait/work/data/leveldb/msncids.ldb"):
        LevelDB.__init__(self, path)

    def readfile(self, filename):
        for line in file(filename):
            line = line.strip()
            if not line:
                continue
            yield line

    def add_file_to_db(self, filename, state='0'):
        ct = 0
        ft = 0
        batch = None
        state = str(state)
        for line in self.readfile(filename):
            if batch is None:
                batch = leveldb.WriteBatch()
            
            if True or self.get(line, None)  is None: 
                batch.Put(line, state)
                ct += 1
            
                if ct % SYNC == 0:
                    self.db.Write(batch, sync = True)
                    batch = None
                    log.trace('filename %s sync new %d skip %d', filename, ct, ft)
            else:
                ft += 1
                if ft % SYNC == 0:
                    log.trace('filename %s skip new %d skip %d', filename, ct, ft)
        return ct

    def add_email_to_db(self, filename, state='0'):
        ct = 0
        ft = 0
        batch = None
        state = str(state)
        for line in self.readfile(filename):
            item = line.split('\t')
            if len(item) < 4:
                ft += 1
                continue
            cid = item[0].strip()
            if len(cid) != 16:
                ft += 1
                continue
            email = item[3].lower()
            if not email or email.find('@') == -1:
                ft += 1
                continue
            ct += 1
            #value = self.get(cid)
            if True:#value is None or (value.find('@') == -1 and ):: 
                self.db.Put(cid, email)
                ct += 1

            
                if ct % SYNC == 0:
                    #self.db.Write(batch, sync = True)
                    log.trace('filename %s sync new %d skip %d', filename, ct, ft)
            else:
                ft += 1
                if ft % SYNC == 0:
                    log.trace('filename %s skip new %d skip %d', filename, ct, ft)
        return ct
        

    def del_file(self, filename):
        ct = 0
        for line in self.readfile(filename):
            try:
                self.db.Delete(line)
            except:
                continue
            ct += 1
        log.trace('filename %s del %d', filename, ct)
        return ct
    
    def export(self, state='0', target_dir='.'):
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        total = 0
        ct = 0
        fct = 0
        f = None
        for k, v in self.db.RangeIter():
            total += 1
            if v.find(state) == -1:
                continue
            if f is None:
                filename = '%s_%d.txt' % (self.TARGET_BASE, fct)
                filename = os.path.join(target_dir, filename)
                f = file(filename, 'w')
                log.trace('open new file %s', f.name)        
            ct += 1
            if state == '@':
                f.write('%s\n' % v)
            else:
                f.write('%s\n' % k)
            if ct % 10000 == 0:
                log.trace('export %s num %d total %d', f.name, ct, total)
            if ct % self.EXPORT_LIMIT == 0:
                f = None
                fct += 1
        return ct
    
    def count(self, state='0'):
        total = 0
        for k, v in self.db.RangeIter():
            if v.find(state) == -1:
                continue
            total += 1
            if total % self.EXPORT_LIMIT == 0:
                print total
        print total
    
    def run(self):
        name = osp.basename(self.dbpath)
        open_log(name, logging.INFO)
        open_debug()
        parser = OptionParser()
        parser.add_option("-a", "--action", dest="action", help="what action[add|del|export|addemail]")
        parser.add_option("-f", "--file", dest="filename",
                      help="write report to add", metavar="FILE")
        parser.add_option("-s", "--state", dest="state", help="what state want to set", type="string")
        parser.add_option('-t', "--target_dir", dest='target_dir', help="which target dir to export")
        parser.add_option('-c', "--count", dest='count', action="store_true")

        options, args = parser.parse_args(sys.argv[1:])
        if options.count:
            return self.count(options.state or '0')
        if options.action == 'export':
            print 'begin export'
            ct = self.export(options.state or '0', options.target_dir)
            return
        
        if not options.filename:
            parser.print_help()
            return
        if osp.isdir(options.filename):
            filenames = [osp.join(options.filename, x) for x in os.listdir(options.filename)] 
        else:
            filenames = [options.filename]
                
        
        if options.action == 'add':             
            total = 0
            for filename in filenames:
                if filename.find('.svn') != -1:
                    continue
                ct = self.add_file_to_db(filename, options.state or 0)
                total += ct
                log.trace('action %s fielname %s result new %d total %d', options.action, filename,  ct, total)
                
        if options.action == 'addemail':             
            total = 0
            for filename in filenames:
                ct = self.add_email_to_db(filename, options.state or 0)
                total += ct
                log.trace('action %s fielname %s result new %d total %d', options.action, filename,  ct, total)

        if options.action == 'del':
            total = 0
            for filename in filenames:
                ct = self.del_file(filename)
                total += ct
                log.trace('action %s fielname %s result new %d total %d', options.action, filename,  ct, total)            
        
        
def main():
    app = MSNCIDSDB()
    app.run()

if __name__ == '__main__':
    main()
