#!/usr/bin/env python2.6
#coding=utf-8
from py3rd.mako.lookup import TemplateLookup
from py3rd.mako import runtime

class Undefined(object):
    def __init__(self, *args, **kwargs):
        pass

    def __getitem__(self, name):
        return Undefined()

    def __getattr__(self, name):
        return Undefined()
    
    def __str__(self):
        return ''

    def __nonzero__(self):
        return False

    def __iter__(self):
        return []
    
    def get(self, name, default=None):
        if default is None:
            return Undefined()
        return default

UNDEFINED = Undefined()
runtime.UNDEFINED = UNDEFINED

class_cache = {}

def auto_wrap_obj(obj):
    if type(obj) == bool or callable(obj) or obj is None:
        return obj
    Storage = class_cache.get(obj.__class__, None)
    if Storage is None:
        class Storage(obj.__class__):
            def __getattribute__(self, name):
                try:
                    res = object.__getattribute__(self, name)
                except AttributeError:
                    try:
                        res = obj.__class__.__getitem__(self, name)
                    except:
                        return UNDEFINED
                return auto_wrap_obj(res)
            
            def __getitem__(self, name):
                try:
                    res = obj.__class__.__getitem__(self, name)
                    return auto_wrap_obj(res)
                except (IndexError, KeyError):
                    return UNDEFINED
                

        class_cache[obj.__class__] = Storage
    return Storage(obj)

def wrap_render(render, initializer={}):
    def _wrap(*args, **kwargs):
        #args = [auto_wrap_obj(x) for x in args]
        
        #for k, v in kwargs.items():
        #    kwargs[k] = auto_wrap_obj(v)
        
        for k, v in initializer.items():
            if k not in kwargs:
                kwargs[k] = v
        
        return render(*args, **kwargs)
    return _wrap


class render_mako:
    """Rendering interface to Mako Templates.

    Example:

        render = render_mako(directories=['templates'])
        render.hello(name="mako")
    """
    def __init__(self, *a, **kwargs):
        self.initializer = kwargs.pop('initializer', {})
        self._lookup = TemplateLookup(*a, **kwargs)

    def __getattr__(self, name):
        # Assuming all templates are html
        path = name + ".html"
        t = self._lookup.get_template(path)
        return wrap_render(t.render, self.initializer)
    

    
