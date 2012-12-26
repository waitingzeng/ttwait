#!/usr/bin/python2.7
# coding=utf8
from pycomm.db.mysql import Connection,IntegrityError 
from pycomm.log import log

class AccountModel(object):
    def __init__(self, *args, **kwargs):
        try:
            self.db = Connection(*args, **kwargs)
        except:
            self.db = None

    def __setitem__(self, account, state):
        acc = self.db.accounts
        try:
            acc.insert(account=account, state=state)
        except IntegrityError:
            if state == -1:
                sql = "update accounts set state = %(state)d where account='%(account)s'" % locals()
            else:
                sql = "update accounts set state = %(state)d where account='%(account)s' and state < %(state)d and state != -1" % locals()
            self.db.execute(sql)
        return True
    
    def get_action_num(self, action=None):
        if action is None:
            return 0
        row = self.db.get("select * from actions where action='%s' limit 1" % action)
        if row is None:
            return 0
        return row['num']
    
    def update_action_num(self, action, num):
        if action is None:
            return
        try:
            sql = "insert into actions (action, num) values ('%s', %s)" % (action, num)
            self.db.execute(sql)
        except IntegrityError:
            sql = "update actions set num = %d where action='%s'" % (num, action)
            self.db.execute(sql)

    def get_accounts(self, begin=None, state=None, create_time=None, limit = 10000, **kwargs):
        log.trace('get_accounts %s ', begin)
        params = []
        sql = "select * from accounts where "
        if begin is not None:
            sql += 'id > %d' % begin
        
        if state is not None:
            if state < 1:
                sql += ' and state = %d' % state
            else:
                sql += ' and state >= %d' % state
        else:
            sql += ' and state != -1'

        if create_time is not None:
            sql += ' and create_time <= %s '
            params.append(create_time)
        
        for k, v in kwargs.items():
            if v is None:
                continue
            sql += ' and %s = %%s ' % (k)
            params.append(v)

        sql += ' order by id limit %d' % limit
        log.debug("sql %s params %s", sql, params)
        return self.db.query(sql, *params)

    def get_iter(self, action=None, state=None, *args, **kwargs):
        last_id = self.get_action_num(action)
        log.trace('get_iter for action %s from %s', action, last_id)
        while True:
            had_item = False
            
            for row in self.get_accounts(last_id, state, *args, **kwargs):
                yield row
                last_id = row.id
                had_item = True
            if not had_item:
                self.update_action_num(action, 0);
                break 

    def set_can_add(self, limit=0):
        if limit > 0:
            sql = "update accounts set can_add=1 where can_add=0 and state>=1 order by id limit %d" % limit
            self.db.execute(sql)
        sql = "select count(id) as num from accounts where can_add=1 and  state>= 1"
        can_add = int(self.db.get(sql)['num'])
        sql = "select count(id) as num from accounts where can_add=0 and state=1"
        new_active = int(self.db.get(sql)['num'])
        sql = "select count(id) as num from accounts where state=0"
        new_acc = int(self.db.get(sql)['num'])
        sql = "select count(id) as num from accounts where state>=10"
        can_send = int(self.db.get(sql)['num'])
        sql = "select count(id) as num from accounts where state=-1"
        login_fail = int(self.db.get(sql)['num'])
        return {'can_add' : can_add, 'new_active' : new_active, 'new_acc' : new_acc, 'can_send' : can_send, 'login_fail' : login_fail}

