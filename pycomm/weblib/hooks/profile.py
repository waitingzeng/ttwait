#! /usr/bin/env python
#coding=utf-8
import cProfile
from cStringIO import StringIO
import sys
from py3rd import webpy
from pycomm.utils.decorators import get_std_output

def _processor(handler):
    if webpy.input().get('prof', None) is not None:
        profiler = cProfile.Profile()
        profiler.runcall(handler)
        profiler.create_stats()
        res, output = get_std_output(profiler.print_stats)('time')
        return '<pre>%s</pre>' % output
    else:
        return handler()

def create_hook(app):
    app.add_processor(_processor)
