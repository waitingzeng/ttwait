#!/bin/env python
#coding=utf-8
import json
from PyQt4.QtCore import pyqtSlot

from pyphantomjs import webpage

class WebPage(webpage.WebPage):
    #@pyqtSlot(str, result='QVariant')
    def evaluate(self, code, *args):
        if not args:
            function = '(%s)()' % code
        else:
            function = '(%s)(%s)' % (code, json.dumps(args)[1:-1])
        return self.m_mainFrame.evaluateJavaScript(function)


