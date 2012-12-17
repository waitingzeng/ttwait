#!/bin/env python
#coding=utf-8
import os
import sys

from pycomm.log import log, open_log, open_debug
from pycomm.libs.rpc import MagicClient
from pycomm.utils.dict4ini import DictIni
from optparse import OptionParser



def load():
    open_log("load account")
    open_debug()
    parser = OptionParser()
    parser.add_option("-i", "--conf", dest="conf", action="store", type="string")
    parser.add_option("-n", "--num", dest="num", action="store", type="int")
    parser.add_option("-t", "--target", dest="target", action="store", type="string")

    options, args = parser.parse_args(sys.argv[1:])
    if not options.conf or not options.target:
        parser.print_help()
        sys.exit(-1)

    conf = DictIni(options.conf)
    num = options.num or 100000
    if os.path.exists(options.target):
        log.error("%s had exitst", options.target)
        return
    
    client = MagicClient(conf.account_server[0], int(conf.account_server[1]))
    total = 0
    f = file(options.target, 'w')
    log.trace("begin load data")
    while total < num:
        data = client.get_add_friends()
        if data:
            total += len(data)
            f.write('\n'.join([x.strip() for x in data]))
            log.trace("load account success %s", total)
        elif not data and not total:
            log.trace("load account %s fail")
            break
    f.close()
    log.trace("load accounts %s success %s", len(data), total)
    


if __name__ == "__main__":
    load()


