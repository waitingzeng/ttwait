#!/usr/bin/env python

from py3rd import webpy
from urls import urls
app = webpy.application(urls, globals())
application = app.wsgifunc()

if __name__ == "__main__":
    from pycomm.weblib.shortcut import debug_server
    debug_server(app)
