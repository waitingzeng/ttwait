#! /usr/bin/env python
#coding=utf-8
import sys
import re
import time
import os
import os.path as osp
from random import randint, randrange
import traceback
import hashlib
import pycomm.signal as mysignal
from pycomm.log import log
import string

def get_in(data, b, e=None, start=0, flag=False):
    if data is None:
        return None
    b1 = data.find(b, start)
    if b1 == -1:
        return None
    b1 += len(b)
    if e is None:
        return data[b1:]
    if isinstance(e, list):
        e1 = -1
        for i in range(b1 + 1, len(data)):
            if data[i] in e:
                e1 = i
                break
    else:
        e1 = data.find(e, b1)
    if e1 == -1:
        if flag:
            return data[b1:]
        return None
    return data[b1:e1]


def get_in_list(data, b, e, start=0):
    if data is None:
        return
    while True:
        b1 = data.find(b, start)
        if b1 == -1:
            return
        b1 += len(b)
        e1 = data.find(e, b1)
        if e1 == -1:
            return
        yield data[b1:e1]
        start = e1


def xreadlines(filename, comment=None):
    if os.path.exists(filename):
        with file(filename) as pipe:
            for x in pipe:
                x = x.strip()
                if x and (not comment or not x.startswith(comment)):
                    yield x

def readlines(*args, **kwargs):
    return list(xreadlines(*args, **kwargs))

def readdict(filename, sp = None, ignore=True):
    data = {}
    if os.path.exists(filename):
        with file(filename) as pipe:
            for x in pipe:
                x = x.strip()
                if x:
                    if sp is None:
                        data[x] = 1
                    else:
                        try:
                            k,v = x.split(sp, 2)
                            data[k.strip()] = v.strip()
                        except Exception, info:
                            if not ignore:
                                raise info
                            print info
                            continue
    return data


def writelines(filename, lines):
    if lines is None:
        return
    with file(filename, 'w') as a:
        a.write('\n'.join(lines))
        a.write('\n')


class CacheFile(object):
    def __init__(self, filepath, lock=None):
        self.filepath = filepath
        if not os.path.exists(self.filepath):
            raise Exception('%s does not exists' % self.filepath)
        self.data = []
        self.lock = lock
        self._init()

    def _init(self):
        if not self.data:
            self.data = readlines(self.filepath)
            if not self.data:
                raise Exception("not data found by %s", self.filepath)

    def get(self, index=0):
        if not self.lock:
            self._init()
            return self.data.pop(index)
        else:
            with self.lock:
                self._init()
                return self.data.pop(index)

    def next(self):
        return self.get()
    
    def __getitem__(self, index):
        return self.get(index)

    def get_rnd(self):
        self._init()
        index = randrange(0, len(self.data))
        return self.get(index)

def rnd_str(num):
    if not num:
        return ''
    result = []
    for i in range(num):
        result.append(chr(randint(97,122)))
    return ''.join(result)

letters = '0123456789' + string.ascii_letters
def rnd_letters(num):
    if not num:
        return ''
    result = []
    l = len(letters)
    for i in range(num):
        result.append(letters[randrange(0, l)])
    return ''.join(result)

def force_unicode(s):
    if isinstance(s, unicode):
        return s
    try:
        s = s.decode('gbk')
        if isinstance(s, unicode):
            return s
    except:
        pass

    try:
        s = s.decode('utf-8')
        if isinstance(s, unicode):
            return s
    except:
        pass
    try:
        import chardet
        res = chardet.detect(s)
        try:
            s = s.decode(res['encoding'])
            if isinstance(s, unicode):
                return s
        except:
            pass
    except:
        pass
    return s


def md5(s):
    a = hashlib.md5(s)
    return a.hexdigest()

smart_split_re = re.compile('("(?:[^"\\\\]*(?:\\\\.[^"\\\\]*)*)"|\'(?:[^\'\\\\]*(?:\\\\.[^\'\\\\]*)*)\'|[^\\s]+)')
def smart_split(text):
    r"""
    Generator that splits a string by spaces, leaving quoted phrases together.
    Supports both single and double quotes, and supports escaping quotes with
    backslashes. In the output, strings will keep their initial and trailing
    quote marks.

    >>> list(smart_split(r'This is "a person\'s" test.'))
    [u'This', u'is', u'"a person\\\'s"', u'test.']
    >>> list(smart_split(r"Another 'person\'s' test."))
    [u'Another', u"'person's'", u'test.']
    >>> list(smart_split(r'A "\"funky\" style" test.'))
    [u'A', u'""funky" style"', u'test.']
    """
    for bit in smart_split_re.finditer(text):
        bit = bit.group(0)
        if bit[0] == '"' and bit[-1] == '"':
            yield '"' + bit[1:-1].replace('\\"', '"').replace('\\\\', '\\') + '"'
        elif bit[0] == "'" and bit[-1] == "'":
            yield "'" + bit[1:-1].replace("\\'", "'").replace("\\\\", "\\") + "'"
        else:
            yield bit

def waitexit(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except:
            log.exception('')
        raw_input('press any key to exit')
    return wrapper



def sleep(sec=0):
    
    a = time.time()
    log.trace('waiting')
    while mysignal.ALIVE:
        b = sec - (time.time() - a)
        if b <= 0:
            break
        log.trace('wainting %s ', int(b))
        try:
            time.sleep(10)
        except:
            break



def force_write(filename, content, mode='wb'):
    path = osp.dirname(osp.abspath(filename))
    if not osp.exists(path):
        os.makedirs(path)
    return file(filename, mode).write(content)

if __name__=='__main__':
    #print list(smart_split(u'被上诉人 (原审原告): 张某某, 女.'))
    print get_yahoo_tags("make money")

