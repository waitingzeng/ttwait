# coding: utf-8
#from pycomm.db.level import LevelDB
from pycomm.libs.rpc import MagicServer, MagicClient
import sys
from pprint import pprint
from pycomm.log import log
from accountmodel import AccountModel
from tosdata import TosData

class AccountServer(MagicServer):
    def __init__(self, port, **kwargs):
        MagicServer.__init__(self, port)
        self.db = AccountModel(**kwargs)
        self.tos_data = TosData()
        for k in dir(self):
            v = getattr(self, k, None)
            if callable(v) and k.endswith('_iter'):
                self.__dict__['_%s' % k] = v()

    def add_account(self, handler, names=[], state=0, kwargs={}):
        if not isinstance(names, list):
            names = [names]
        for name in names:
            log.trace('add account %s state %s', name, state)
            
            self.db[name] = state
        for k, v in kwargs.iteritems():
            log.trace('add account %s state %s', k, v)
            self.db[k] = v
        return True
    
    def new_account_iter(self):
        while True:
            for row in self.db.get_iter(state=0):
                yield row.account
            yield None

    def get_new_account(self, handler):
        try:
            ret = self._new_account_iter.next()
            log.trace('get new account %s', ret)
            return ret
        except:
            return None
    
    def add_friends_iter(self):
        while True:
            for row in self.db.get_iter('add_friends', state=1, can_add=1):
                yield row
            yield None

    def get_add_friends(self, handler, limit=10000):
        res = []
        try:
            while True:
                row = self._add_friends_iter.next()
                if row is None:
                    break
                res.append(row.account)
                if len(res) >= limit:
                    break
            self.db.update_action_num('add_friends', row.id)
            return res
        except StopIteration:
            self.db.update_action_num('add_friends', 0)
            pass
        except:
            log.exception('')
        return res

    def send_accounts_iter(self):
        while True:
            for row in self.db.get_iter('send_accounts', state=2, can_add=1):
                yield row
            yield None

    def get_send_accounts(self, handler, limit=10000):
        res = []
        try:
            while True:
                row = self._send_accounts_iter.next()
                if row is None:
                    break
                res.append(row.account)
                if len(res) >= limit:
                    break
            self.db.update_action_num('send_accounts', row.id)
        except StopIteration:
            self.db.update_action_num('send_accounts', 0)
            pass
        except:
            log.exception('')
            pass
        return res
    

    def set_can_add(self, handler, limit=0):
        return self.db.set_can_add(limit)

    def get_tos_data(self, handler, limit=10000):
        res = []
        for i in xrange(limit):
            try:
                res.append(self.tos_data.get())
            except:
                log.exception('')
                break
        self.tos_data.sync()
        return res


from pycomm.proc.procpool import ProcPool
class Application(ProcPool):
    def work(self, name, id):
        server = AccountServer(self.conf.port, **self.conf.mysql)
        server.start()

    def add_options(self, parser):
        parser.add_option("-c", '--command', dest='command', action="store", help="the command to run", type="string")
        parser.add_option("-h", '--host', dest='host', action="store", help="the host to connect", type="string")

    def init(self):
        if self.options.command:
            host = self.options.host or self.conf.client_host or '127.0.0.1'
            if not host:
                raise Exception('need host')
            cli = MagicClient(host, self.conf.port)
            exec('pprint(cli.%s)' % self.options.command)
            sys.exit(0)

def main():
    app = Application()
    app.run()


def test():
    from pycomm.utils.dict4ini import DictIni
    conf = DictIni('account_server.conf')
    app = AccountServer(11033, **conf.mysql)

if __name__ == '__main__':
    main()


