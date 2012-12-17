import threading
import time
from pycomm.log import log
from .basic import ProcBase

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

    
    def main_loop(self):
        ct = 0
        while threading.activeCount() > 1:
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
