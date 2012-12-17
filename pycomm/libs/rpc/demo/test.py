#!/usr/bin/env python
# coding: utf-8
from pycomm.libs import rpc

class Application(rpc.Application):
    def __init__(self, request_callback):
        sniorfy.rpc.Application.__init__(self, RequestHandler)


class RequestHandler(sniorfy.rpc.RequestHandler):
    def deal(self):
        print self.request.argv
        for arg in self.request.argv:
            self.addarg(arg)


def main():
    app = Application(RequestHandler)
    app.listen(3370)
    app.start()


if __name__ == '__main__':
    main()
