#!/usr/bin/python
#coding=utf8
import os.path as osp

from pycomm.libs.rpc.magicserver import MagicServer, run_server
from pycomm.db.level import LevelDB
from tornado.options import define
from pycomm.utils.escape import json_pickle

define("db_root", type=str, help="the level db path root")
define("pickle_type", type=str, default='none',
       help="the db value pickle type", metavar="none|json")


class Application(MagicServer):
    def init(self, options):
        self.dbs = {}
        self.iters = {}
        if options.pickle_type == 'json':
            self.pickle_type = json_pickle
        else:
            self.pickle_type = None
        self.db_root = options.db_root or '.'

    def get_db(self, db_name):
        if db_name not in self.dbs:
            db = LevelDB(osp.join(self.options.db_root, db_name), self.pickle_type)
            self.dbs[db_name] = db
        return self.dbs[db_name]

    def get_iter(self, db_name):
        if db_name not in self.iters:
            db = self.get_db(db_name)
            self.iters[db_name] = iter(db)
        return self.iters[db_name]

    def get(self, handler, db_name, key, default=None):
        return self.get_db(db_name).get(key, default)

    def set(self, handler, db_name, key, value):
        self.get_db(db_name)[key] = value

    def batch_set(self, handler, db_name, kwargs):
        db = self.get_db(db_name)
        for k, v in kwargs.items():
            db[k] = v

    def delete(self, handler, db_name, key):
        self.get_db(db_name).delete(key)

    def exists(self, handler, db_name, key):
        try:
            self.get_db[db_name][key]
            return True
        except:
            return False

    def set_default(self, handler, db_name, key, value):
        db = self.get_db(db_name)
        if not self.exists(handler, db_name, key):
            db[key] = value

    def next(self, handler, db_name):
        try:
            return self.get_iter(db_name).next()
        except StopIteration, info:
            del self.iters[db_name]
            raise info

    def next_many(self, handler, db_name, num=1):
        res = []
        for i in range(num):
            try:
                res.append(self.next(handler, db_name))
            except:
                break
        return res

def main():
    run_server(Application)

if __name__ == '__main__':
    main()
