#! /usr/bin/env python2.6
#coding=utf-8
import sys
from accounttext import AccountNotMemery

def trunk(name):
    tos = AccountNotMemery(name)
    tos.load()
    tos.trunk()

if __name__ == '__main__':
    trunk(sys.argv[1])