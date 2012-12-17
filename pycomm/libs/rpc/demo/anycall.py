#!/usr/bin/env python
# coding: utf-8
import argparse
from pycomm.libs.rpc import MagicClient


argparser = argparse.ArgumentParser(description='telnet of stp', conflict_handler='resolve')
argparser.add_argument('-h', metavar='host', dest='host', type=str, default='localhost', help='host')
argparser.add_argument('-p', metavar='port', dest='port', type=int, default=3370, help='port')
argparser.add_argument('-s', metavar='socket', dest='socket', type=str, default=None, help='unix socket of sink')
args = argparser.parse_args()


def main():
    mc = MagicClient(args.host, args.port, unix_socket=args.socket)
    print mc.add_account('aaaa')
    print mc.get_new_account()


if __name__ == '__main__':
    main()
