#!/usr/bin/env  python
# coding: utf-8
from pycomm.log import open_log, open_debug
from pycomm.libs.rpc import MagicServer
import sys
import time


class MyServer(MagicServer):
    def func1(self, handler, *args):
        return args

    def func2(self, handler, *args):
        return args

    def ping(self, handler, *args):
        time.sleep(2)
        return 'pong'


def main():
    open_log('anyserver')
    open_debug()
    server = MyServer(int(sys.argv[1]))
    server.start()


if __name__ == '__main__':
    main()
