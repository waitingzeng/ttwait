#!/usr/bin/python2.7
#coding=utf8
import inspect

def get_schema(func):
    def get_schema(self, handle):
        code = inspect.getsourcelines(func)
        def_code = code[0][0]

        if func.__class__.__name__ == 'instancemethod':
            code = '%s.%s' % (func.im_class.__name__, def_code)
        else:
            code = def_code
        if code.__doc__:
            code += '\n' + code.__doc__
        return code
    return get_schema
