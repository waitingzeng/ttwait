#!/bin/env python
#coding=utf-8
import os
from pycomm.log import log
from webpage import WebPage
from pyphantomjs import phantom

class Phantom(phantom.Phantom):
    @phantom.pyqtSlot(result=WebPage)
    def createWebPage(self):
        page = WebPage(self, self.app_args)
        self.m_pages.append(page)
        page.applySettings(self.m_defaultPageSettings)
        page.libraryPath = os.path.dirname(os.path.abspath(self.m_scriptFile))
        return page

    def printConsoleMessage(self, message, lineNumber, source):
        if source:
            message = '%s:%d %s' % (source, lineNumber, message)
        log.info(message)
        print message
