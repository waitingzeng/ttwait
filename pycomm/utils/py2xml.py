#-*- coding: utf-8 -*-

from lingj.packet import utf8

from pycomm.utils.encoding import smart_unicode, smart_str
from array import array

TPL = '''<?xml version="1.0" encoding="utf-8"?>
%s'''

class Buff(object):
    def __init__(self):
        self.buff = array('c')
        
    def append(self, data):
        self.buff.fromstring(smart_str(data))
        
    def get_buff(self):
        return self.buff.tostring()

def handle_tab(buff, deep):
    tab = "\t"*deep
    buff.append(tab)
    
def handle_head(buff, name, deep):
    handle_tab(buff, deep)
    buff.append("<%s>\n"%(name))
    
def handle_end(buff, name, deep):
    handle_tab(buff, deep)
    buff.append("</%s>\n"%(name))    

def dict2xml(dict_name, objects):
    buff = Buff()
    if type(objects) == list:
        handle_list(dict_name, objects, buff)
    else:
        handle_dict(dict_name, objects, buff)
    return TPL % buff.get_buff()    

def handle_list(name, objects, buff, deep=0):
    handle_head(buff, name, deep)
    child_name = name[:-1] if name[-1] == 's' else name
    for obj in objects:
        if type(obj) == dict:
            # remove the 's'
            handle_dict(child_name, obj, buff, deep+1)
        else:
            handle_str(child_name, obj, buff, deep+1)
    handle_end(buff, name, deep)
    deep += 1
    
def handle_dict(name, dict_obj, buff, deep=0):
    handle_head(buff, name, deep)
    for _k, _v in dict_obj.items():
        if type(_v) == list:
            handle_list(_k, _v, buff, deep+1)
        elif type(_v) == dict:
            #handle_list(_k, _v.values(), buff, deep)
            #raise Exception("cannot parse dict in dict")
            handle_dict(_k, _v, buff, deep+1)
        else:
            handle_str(_k, _v, buff, deep+1)
    handle_end(buff, name, deep)
    deep += 1

def handle_str(node_name, dict_obj, buff, deep=0):
    handle_tab(buff, deep)
    
    data =  {"k" : smart_unicode(node_name), "v" : dict_obj} 
    buff.append("<%(k)s>%(v)s</%(k)s>\n"%data)
    
def py2xml(*args, **kwargs):
    return dict2xml(*args, **kwargs)
    
if __name__ == '__main__':
    MAP_STRUCTS = {"monther" : {"name" : "luna", "age" : 17},
                   "girl" : {"name" : "purp", "age" : 16},
                   }
    print dict2xml("address_books", MAP_STRUCTS)
    
    
