import threading
import time
from pycomm.log import log
from .basic import ProcBase
from random import randint

class ThreadBase(ProcBase):
    def _init(self):
        self.sync_times = self.conf.sync_times or 10
        self.wait = self.conf.wait or 30
        self.lock = threading.RLock()
   
    def get_worker_name(self, id):
        return threading.currentThread().getName()
    
    def sync(self):
        pass

    def end(self):
        self.sync()

    def main(self):
        pass

    def after_run_worker(self,name, id):
        self.create_worker(id)

    def main_loop(self):
        ct = 0
        time.sleep(3)
        while threading.activeCount() > 1:
            tc = threading.activeCount()
            if tc < (self.worker_num + 1):
                self.create_worker(randint(100, 100000))
            try:
                if self.wait:
                    time.sleep(self.wait)
                ct += 1
                if ct >= self.sync_times:
                    self.sync()
                    ct = 0
                    log.trace('current thread %s', threading.activeCount())
                self.main()
            except KeyboardInterrupt:
                break
            except:
                log.exception('had some error')
                continue

        self.end()

    def create_worker(self, id):
        h = threading.Thread(target=self.worker, name='Thread%2d' % id, args=(id,))
        h.setDaemon(True)
        h.start()
