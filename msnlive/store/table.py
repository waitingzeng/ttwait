#! /usr/bin/env python
#coding=utf-8

from dict4ini import DictIni
from db.mysql import DB
from itertools import cycle
import mysignal
import threading


class Store(object):
    TABLEPREV = list('0123456789abcdef')
    def __init__(self, config):
        self.config = config
        self.maxid = {}
        self.tablelist = cycle(self.TABLEPREV)
        self.current = self.tablelist.next()
        self.db = self.get_db()
        #self.create_table()
        self.users = []
        self.lock = threading.RLock()

    def create_table(self):
        for k in self.TABLEPREV:
            sql = """CREATE TABLE IF NOT EXISTS `user_%s` (
`id` INT( 11 ) NOT NULL AUTO_INCREMENT,
`name` CHAR( 16 ) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL ,
`state` TINYINT UNSIGNED NOT NULL default 0,
PRIMARY KEY (  `id` ) ,
UNIQUE (`name`))
ENGINE = MYISAM CHARACTER SET utf8 COLLATE utf8_general_ci""" % k
            self.db.execute(sql)


    def get_db(self):
        DEFAULT = {
            'charset': 'gbk',
            'use_unicode': False,
            'host' : self.config.mysql.host,
            'user' : self.config.mysql.user,
            'passwd' : self.config.mysql.passwd,
        }
        try:
            return DB(self.config.mysql.dbname, **DEFAULT)
        except:
            import traceback
            traceback.print_exc()
            return None

    def load(self, limit=10000):
        if len(self.users) > 100:
            return
        ct = 0
        while mysignal.ALIVE and ct < len(self.TABLEPREV):
            ct += 1
            maxid = self.maxid.setdefault(self.current, 0)
            sql = "select id, name from user_%s where state=0 and id>%s order by id limit %s" % (self.current, maxid, limit)
            data = self.db.execute_all(sql)
            if len(data):
                for user in data:
                    self.users.append(user[1])
                self.maxid[self.current] = data[-1][0]
                return
            else:
                self.current = self.tablelist.next()

    def export(self, filename):
        f = file(filename, 'w')
        for t in self.TABLEPREV:
            sql = "select id, name from user_%s where state=1" % t
            data = self.db.execute_all(sql)
            if len(data):
                for user in data:
                    f.write(user[1])
                    f.write('\n')
                f.flush()
            sql = "update user_%s set state=3 where state=1" % t
            self.db.execute(sql)
        f.close()


    def get(self):
        with self.lock:
            return self.users.pop()

    def __len__(self):
        return len(self.users)

    def save(self, user, names=None):
        try:
            if names:
                for name in names:
                    name = name.lower().strip()
                    sql = "insert ignore user_%s (name) values ('%s')" % (name[-1], name)
                    self.db.execute(sql)

            if user is not None:
                if not names:
                    state = 2
                else:
                    state = 1
                sql = "update user_%s set state=%s where name='%s'" % (user[-1], state, user)
                self.db.execute(sql)
        except Exception, info:
            if str(info).lower().find('lost connection') != -1:
                self.db = self.get_db()
                self.save(user, names)


if __name__ == '__main__':
    config = DictIni('../config.ini')
    app = Store(config)
    while True:
        app.load()
        try:
            for i in app.get():
                print i
        except:
            continue