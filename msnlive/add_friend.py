#! /usr/bin/env python
#coding=utf-8
from gevent import monkey
monkey.patch_all()

from webmsnlib.add_thread import add_friend as main
import traceback
import sys

if __name__ == '__main__':
    from pycomm.log import open_debug
    open_debug()
    
    main()
