#! /usr/bin/env python
#coding=utf-8
from py3rd.webpy.utils import Storage

def safe_int(x, base=10, default=0):
    try:
        return int(str(x), base)
    except:
        return default

def safe_str(x, default=''):
    try:
        return str(x)
    except:
        return default


class SafeInput(Storage):
    def get_value(self, name):
        v = self.get(name, '')
        if isinstance(v, list):
            return v[-1]
        return v
    
    def get_list(self, name):
        v = self.get(name, '')
        if not v:
            return []
        if isinstance(v, list):
            return v
        return [v]

    def get_str(self, name, default=''):
        try:
            return str(self.get_value(name))
        except:
            return default
    
    def get_int(self, name, base=10, default=0):
        return safe_int(self.get_value(name), base, default)
        
    def get_str_list(self, name, default=''):
        return [str(x) for x in self.get_list(name)]

    def get_int_list(self, name, base=10, default=0):
        return [safe_int(x, base, default) for x in self.get_list(name)]
