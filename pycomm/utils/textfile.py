#! /usr/bin/env python
#coding=utf-8
from __future__ import with_statement
import threading
import os
import os.path as osp
import shutil
import glob
from random import randint, shuffle, randrange, choice
import traceback
import tempfile
import sys
from pycomm.log import log
from pycomm import signal as mysignal
from pycomm.utils.text import readlines, writelines, readdict


class NotDataException(Exception):pass

class CacheText(object):
    def __init__(self, path, once = False, cache=True, clear_file = None, force_local=True):
        self.path = path
        self.basedir = osp.dirname(path)
        self.name = osp.basename(path)
        self.get_num = 0

        if not osp.exists(self.path):
            log.error("%s not exists", self.path)
            raise NotDataException('%s not exists', self.path)
        
        self.local_file = '%s.local' % self.path

        self.data = []
        self.lock = threading.RLock()
        self.once = once
        self.cache = cache
        self.force_local = force_local
        self.clear_file = clear_file or '%s.clear' % self.path
        self.clear_file = file(self.clear_file, 'w')
        
        self.load()

        
    def update_local(self):
        if osp.exists(self.local_file):
            a = os.stat(self.path).st_mtime
            b = os.stat(self.local_file).st_mtime
            if b < a:
                os.unlink(self.local_file)

    def clear_local(self):
        if osp.exists(self.local_file):
            os.unlink(self.local_file)

    def load(self):
        if len(self.data):
            return
        self.sync()
        if self.cache:
            self.update_local()
            
        if self.force_local and os.path.exists(self.local_file):
            self.data = readlines(self.local_file)

        if not self.data:
            self.data = readlines(self.path)
        if len(self.data) == 0:
            raise NotDataException
        self.clear()
        self.change = True
        self.sync()
    
    def clear(self):
        if self.clear_file:
            if osp.exists(self.clear_file.name):
                out = readdict(self.clear_file.name)
            self.data = [x for x in self.data if x not in out]
    


    def get(self, index=0):
        with self.lock:
            if not self.once:
                self.load()

            if not self.data:
                raise NotDataException

            if index == -1:
                index = randrange(0, len(self.data))

            res = self.data.pop(index)
            self.get_num += 1
            if self.get_num > 10000:
                log.trace("get new %s left %s ", self.get_num, len(self.data))
                self.sync()
            return res

    def get_rnd(self):
        return self.get(-1)

    
    def set(self, items):
        if isinstance(self.clear_file, str):
            self.clear_file = file(self.clear_file, 'a')
            
        if not isinstance(items, (list, tuple)):
            items = [items]
        items.append('')
        self.clear_file.write('\n'.join(items))
        self.clear_file.flush()
        self.change = True
    
    set_fail = set

    def append(self, item):
        if isinstance(item, (list, tuple)):
            self.data.extend(item)
        else:
            self.data.append(item)
    
    def sync(self):
        if not self.get_num:
            return
        self.get_num = 0
        self.clear_file.flush()
        if not self.cache and not self.force_local:
            return
        writelines(self.local_file, self.data)
    
    def remove(self, *args, **kwargs):
        self.set(*args, **kwargs)
        
    def __len__(self):
        return len(self.data)

    def __del__(self):
        self.sync()

class CacheTextNotMemberyBase(object):
    def __init__(self, path, *args, **kwargs):
        self.path = path
        self.basedir = osp.dirname(self.path)
        self.name = osp.basename(self.path)
        if not osp.exists(self.path):
            raise Exception('%s not exists' % self.path)
        self.lock = threading.RLock()
        self.init(*args, **kwargs)
        self.load()
    
    def init(self, *args, **kwarfgs):
        pass
    
    def load(self, *args, **kwargs):
        pass
    
    def sync(self, *args, **kwargs):
        pass
    
    def append(self, *args, **kwargs):
        pass

class RandomTextNotMembery(CacheTextNotMemberyBase):
    def init(self, autoreload=True):
        self.autorelead = autoreload
        self.tmpname = None
        self.tmpfile = None
        self.len = 0
    
    def load(self):
        self.close()
        self.tmpname = tempfile.mktemp()
        lines = file(self.path).readlines()
        self.len = len(lines)
        shuffle(lines)
        a = file(self.tmpname, 'w')
        a.writelines(lines)
        a.close()
        self.tmpfile = file(self.tmpname)
    
    def get_nolock(self):
        try:
            return self.tmpfile.next().strip()
        except StopIteration:
            self.load()
            return self.tmpfile.next().strip()
            
    
    def get(self):
        with self.lock:
            try:
                return self.tmpfile.next().strip()
            except StopIteration:
                self.load()
                return self.tmpfile.next().strip()

    def __len__(self):
        return self.len
    
    def close(self):
        if hasattr(self, 'tmpname') and self.tmpname:
            try:
                if not self.tmpfile.closed:
                    self.tmpfile.close()
                os.unlink(self.tmpname)
            except:
                pass
            self.tmpname = None

    def __del__(self):
        self.close()
            

class CacheTextNotMemery(CacheTextNotMemberyBase):
    SYNC_LIMIT = 10000
    def init(self, line_len=None, need_append=False):
        self.info_path = '%s.info' % self.path
        self.append_path = '%s.append' % self.path
        self._line = 0
        self._total_len = 0
        self.line_len = line_len or 1
        if need_append:
            self._append = file(self.append_path, 'a')
        else:
            self._append = None
        
        self.get_num = 0    

    def load(self):
        stat = os.stat(self.path)
        self.total_len = stat.st_size
        self._main_file = file(self.path)
        
        self._line = self.get_info()
        for i in xrange(self._line):
            try:
                self._main_file.next()
            except StopIteration:
                raise NotDataException
    
    def get(self):
        with self.lock:
            try:
                line = self._main_file.next().strip()
            except StopIteration:
                raise NotDataException
            self._line += 1
            if not line:
                return self.get()
            self.get_num += 1
            if self.get_num > self.SYNC_LIMIT:
                self.sync()
            return line
    
    def get_info(self):
        try:
            f = file(self.info_path)
            a = f.read()
            f.close()
            return int(a)
        except:
            return 0
    

    def sync(self, num=None):
        log.trace('%s sync : curline %s', self.path, self._line)
        self.get_num = 0
        f = file(self.info_path, 'w')
        if num is None:
            f.write(str(self._line))
        else:
            f.write(str(num))
        f.close()
        if self._append:
            self._append.flush()
        
    def __len__(self):
        return (self.total_len - 1) / (self.line_len + 1) + 1 - self._line
        
    def append(self, s):
        if self._append:
            with self.lock:
                self.check_file()
                self._append.write(s)
                self._append.write('\n')
    
    
    def remove(self, p):
        if os.path.exists(p):
            os.unlink(p)

    def unlink(self):
        if self._append:
            self._append.close()
        self._main_file.close()
        for f in [self.info_path, self.path]:
            self.remove(f)


class CacheDirText(object):
    def __init__(self, filename, data_dir='data'):
        self.data_dir = data_dir
        self.filename = filename
        self.cur_tos = osp.join(self.data_dir, self.filename + '.txt')
        self.cur_dir = osp.abspath('.')
        try:
            self.cache = CacheTextNotMemery(self.cur_tos)
        except:
            self.init_data()

    def init_data(self):
        
        os.chdir(self.data_dir)
        data_files = glob.glob('%s_*.txt' % self.filename)
        if not data_files:
            log.trace('not find data files, need to un tgz')
            for tgzfile in glob.glob('%s_*.txt.tgz' % self.filename):
                os.popen('tar xzvf %s' %  tgzfile).read()
                log.info("init_data untgz tos %s", tgzfile)
        
        data_files = glob.glob('%s_*.txt' % self.filename)
        if not data_files:
            log.error("not found any data file")
            raise NotDataException
        
        f = choice(data_files)
        shutil.move(f, self.filename)
        try:
            self.cache.unlink()
        except:
            pass
        os.chdir(self.cur_dir)
        self.cache = CacheTextNotMemery(self.cur_tos)


    def next(self):
        
        try:
            ret = self.cache.get()
            return ret
        except:
            self.init_data()
            return self.tos.get()
    get = next

    def sync(self):
        self.cache.sync()


def test():
    from pycomm.log import open_log, open_debug
    open_debug()
    app = CacheText('/Users/ttwait/work/code/python/msnlive/dumps/a.txt', once=True)
    print app.get_rnd()
    print app.get_rnd()

        
if __name__ == '__main__':
    test()


