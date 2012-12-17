#! /usr/bin/env python
#coding=utf-8
from __future__ import with_statement
import threading
import os
from random import randint, shuffle
import mysignal
import traceback
import tempfile
import sys
from pycomm.log import log
from pycomm.utils.text import readlines, writelines, readdict


class NotDataException(Exception):pass

class AccountText(object):
    BASEDIR = 'data'
    def __init__(self, name='sender', once = False, cache=True, other_file = None, clear_data=None):
        if not os.path.exists(name) or os.path.isdir(name):
            self.name = name
            self.local_file = '%s/%s.txt' % (self.BASEDIR, name)
            self.cache_file = '%s/cache_%s.txt' % (self.BASEDIR, name)
        else:
            self.cache_file = name
            path, fname = os.path.split(name)
            self.name = fname
            self.BASEDIR = path
            self.local_file = os.path.join(path, 'local_%s' % fname)
            
            
        self.data = []
        self.lock = threading.RLock()
        self.change = False
        self.once = once
        self.cache = cache
        self.other_file = other_file
        self.clear_data = clear_data or '%s/%s_clear.txt' % (self.BASEDIR, name)
        self.clear_file = self.clear_data

    def create_cache(self):
        if os.path.exists(self.cache_file):
            return self.update_cache()
        else:
            raise NotDataException
    
    def update_cache(self):
        if os.path.exists(self.local_file):
            a = os.stat(self.cache_file).st_mtime
            b = os.stat(self.local_file).st_mtime
            if b < a:
                os.unlink(self.local_file)
                self.change = True

    def load(self):
        if len(self.data):
            return
        if self.cache:
            self.create_cache()
            
        if os.path.exists(self.local_file):
            self.data = readlines(self.local_file)
        if len(self.data) == 0 and self.cache:
            self.data = readlines(self.cache_file)
            if self.other_file and os.path.exists(self.other_file):
                self.data.extend(readlines(self.other_file))
        if len(self.data) == 0:
            raise NotDataException
        self.clear()
        self.change = True
        self.sync()
    
    def clear(self):
        if self.clear_data:
            if os.path.exists(self.clear_data):
                out = readdict(self.clear_data)
            else:
                out = self.clear_data
            self.data = [x for x in self.data if x not in out]
            

    def get(self, *args, **kwargs):
        with self.lock:
            self.change = True
            res = self._get(*args, **kwargs)
            return res
    
    def _get(self, limit=1, sep=None, sort=0):
        if limit == 0:
            return None
        r = []
        for i in range(limit):
            if len(self.data) == 0:
                if self.once:
                    raise NotDataException
                else:
                    if self.cache:
                        self.sync()
                    self.load()
            item = self._get_one(sort)
            r.append(item.strip())
                
        if len(r) == 0:
            return None
        self.had = True
        if limit == 1:
            return r[0]
        if sep is not None:
            return sep.join(r)
        return r
    
    def _get_one(self, sort=0):
        if sort:
            return self.data.pop(0)
            
        return self.data.pop(randint(0, len(self.data)-1))
    
    def set(self, items):
        if self.clear_file is None:
            return
        if isinstance(self.clear_file, str):
            try:
                self.clear_file = file(self.clear_file, 'a')
            except:
                return
        
        if not isinstance(self.clear_file, file):
            return
        
        if not isinstance(items, (list, tuple)):
            items = [items]
        items.append('')
        self.clear_file.write('\n'.join(items))
        self.clear_file.flush()
        self.change = True
    
    def append(self, item):
        if isinstance(item, (list, tuple)):
            self.data.extend(item)
        else:
            self.data.append(item)
    
    def sync(self):
        if not self.change:
            return
        if isinstance(self.clear_file, file):
            self.clear_file.flush()
        writelines(self.local_file, self.data)
    
    def remove(self, *args, **kwargs):
        self.set(*args, **kwargs)
    
    def reset(self):
        return
    
    def __len__(self):
        return len(self.data)

class AccountTextFunc(AccountText):
    def __init__(self, *args, **kwargs):
        self.func = kwargs.pop('func', lambda *a, **kw:True)
        super(self.__class__, self).__init__(self, *args, **kwargs)
        self.lock2 = threading.RLock()
        self.func_limit = 40
        limit = kwargs.pop('limit', 1)
        sep = kwargs.pop('sep', None)
        self._func = self.get_by_func(limit, sep)
    
    def get_by_func(self, limit=1, sep=None):
        i = 0
        while mysignal.ALIVE:
            uids = self.get2(self.func_limit)
            i += 1
            if i >= 5:
                self.sync()
                i = 0
            res = self.func(self, uids)
            for item in res:
                yield item

    
    def get(self, func=True, **kwargs):
        if func:
            with self.lock2:
                try:
                    return self._func.next()
                except NotDataException, info:
                    raise info
                except Exception, info:
                    traceback.print_exc()
                    raise NotDataException
        else:
            return self.get2(**kwargs)
    
    def get2(self, *args, **kwargs):
        return super(self.__class__, self).get(*args, **kwargs)
    
    
    def remove_cache(self):
        if os.path.exists(self.cache_file):
            os.unlink(self.cache_file)
                    
        if os.path.exists(self.senders.local_file):
            os.unlink(self.senders.local_file)

class AccountNotMemberyBase(object):
    BASEDIR = 'data'
    def __init__(self, name, *args, **kwargs):
        self.path = os.path.join(self.BASEDIR, '%s.txt' % name)
        if not os.path.exists(self.path):
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

class RandomAccountNotMembery(AccountNotMemberyBase):
    def init(self, autoreload=True):
        self.autorelead = autoreload
        self.tmpname = None
        self.tmpfile = None
        self.len = 0
        #tempfile.tempdir = os.path.dirname(self.path)
    
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
            

class AccountNotMemery(AccountNotMemberyBase):
    def init(self, line_len=None, need_append=False):
        basename = self.path[:-4]
        self.info_path = '%s.info' % basename
        self.append_path = '%s.append' % basename
        self.trunk_path = '%s.trunk' % basename
        self._line = 0
        self._total_len = 0
        self.line_len = line_len or 1
        if need_append:
            self._append = file(self.append_path, 'a')
        else:
            self._append = None
    
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
        f = file(self.info_path, 'w')
        if num is None:
            log.debug('write back %s', self._line)
            f.write(str(self._line))
        else:
            log.debug('write back %s', num)
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
    
    def trunk(self):
        if self.get_info() == 0:
            return
        f = file(self.trunk_path, 'w')
        for line in self._main_file:
            f.write(line)
        f.close()
        self._main_file.close()
        self.remove(self.path)
        self.sync(0)
        os.rename(self.trunk_path, self.path)
        self.load()
        if self.total_len == 0:
            raise NotDataException('trunk')
    
    def remove(self, p):
        if os.path.exists(p):
            os.unlink(p)

    def unlink(self):
        if self._append:
            self._append.close()
        self._main_file.close()
        for f in [self.trunk_path, self.info_path, self.path]:
            self.remove(f)
        
if __name__ == '__main__':
    RandomAccountNotMembery.BASEDIR = '.'
    a = RandomAccountNotMembery(sys.argv[1])
    print a.get()
    print a.get()
