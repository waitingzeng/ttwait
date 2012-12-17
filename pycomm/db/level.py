from pycomm.log import log

from pycomm.utils import text
import leveldb
import os
import os.path as osp
class NotDefault(object):
    pass

class LevelDB(object):
    def __init__(self, path, pickle=None):
        lock_path = osp.join(path, 'LOCK')
        if osp.exists(lock_path):
            os.unlink(lock_path)
        self.db = leveldb.LevelDB(path)
        self.dbpath = path
        self.pickle = pickle
    
    def _dumps(self, value):
        if self.pickle:
            return self.pickle.dumps(value)
        else:
            return str(value)

    def _loads(self, value):
        if self.pickle:
            return self.pickle.loads(value)
        else:
            return value

    def __getattr__(self, name):
        return getattr(self.db, name)

    def __getitem__(self, key):
        v = self.db.Get(key)
        return self._loads(v)
    
    def __setitem__(self, key, value):
        value = self._dumps(value)
        return self.db.Put(key, value)

    def __delitem__(self, key):
        return self.db.Delete(key)

    def __iter__(self):
        for k, v in self.db.RangeIter():
            yield k, self._loads(v)
    
    def __contains__(self, key):
        try:
            self.db.Get(key)
            return True
        except KeyError:
            return False

    def get(self, key, default=NotDefault):
        try:
            return self[key]
        except:
            if default != NotDefault:
                return default
            raise

    def setdefault(self, key, default):
        try:
            return self[key]
        except:
            self[key] = default
            return default
    
    def setall(self, maps, sync=True):
        batch = leveldb.WriteBatch() 
        for k, v in maps.iteritems():
            batch.Put(k, self._dumps(v))
        self.db.Write(batch, sync = sync)
        return True
    
    def batch_get(self, keys):
        for k in keys:
            try:
                yield self[k]
            except:
                yield None
    
    def export(self, filename, filter=None):
        f = file(filename, 'w')
        ct = 0
        fail = 0
        for k, v in self.db.RangeIter():
            if filter and not filter(k, v):
                fail += 1
                continue
            f.write('%s\t%s\n' % (k, v))
            ct += 1
            if ct % 10000 == 0:
                log.trace("export to %s success %s fail %s", filename, ct, fail)
        f.close()
        return ct, fail

    def load(self, filename, filter=None, default=NotDefault):
        ct = 0
        fail = 0
        for ct, line in enumerate(text.xreadlines(filename)):
            try:
                k, v = line.split('\t',1)
            except:
                if default != NotDefault:
                    k = line
                    v = default
                else:
                    log.error("load from %s line %s:%s format error", filename, ct, line)
                    fail += 1
                    continue
            k, v = k.strip(), v.strip()
            if filter:
                try:
                    oldvalue = self[k]
                    if not filter(k, v, oldvalue):
                        fail += 1
                        continue
                except:
                    pass
            self[k] = v

    def sync(self):
        pass



if __name__ == '__main__':
    app = LevelDB('/tmp/testdb')
    print 'a' in app
