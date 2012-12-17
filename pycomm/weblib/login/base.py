#! /usr/bin/env python
#coding=utf-8
from py3rd import webpy
from pycomm.weblib.base_request import BaseRequest as OldBase

class BaseRequest(OldBase):
    APPNAME = 'login'
    SETTINGS = None
    
    def extra_init(self):
        return {'settings' : self.settings}

