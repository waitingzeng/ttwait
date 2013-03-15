#!/usr/bin/env python
#coding=utf-8
from dict4ini import DictIni
import time
#import adsl
import mysignal
from site_config import SiteUrl
import re
from pycomm.proc.threadbase import ThreadBase

config = DictIni('config.ini')
mylock = threading.RLock()
mylock_page = threading.RLock()
COUNTRE = re.compile(r"<span class='countClass'>([^<]*)</span>", re.I | re.M)
ITEMIDRE = re.compile(r"/(\d+)\?", re.I | re.M)
NUMRE = re.compile(r"[^\d]+", re.I | re.M)

headers = {
    'Accept-Encoding': 'gzip',
    'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)'
}


class Pages:
    dir = 'pages'

    def __init__(self, name):
        self.name = name
        self.filename = '%s/%s.txt' % (self.dir, name)
        self.pages = {}
        if os.path.exists(self.filename):
            a = file(self.filename).read().split(',')
            for x in a:
                if x:
                    self.pages[int(x)] = 0
        self.file = file(self.filename, 'a')
        self.mylock = threading.RLock()
        self.nextpage = self._next()
        self.count = 0

    def add_page(self, p):
        if p not in self.pages:
            self.pages[p] = 0
            self.file.write('%s,' % p)
            self.count += 1
            if self.count >= 10:
                self.file.flush()
                self.count = 0

    def _next(self):
        i = 1
        for i in xrange(1, 10000):
            if i not in self.pages:
                yield i

    def next(self):
        self.mylock.acquire()
        try:
            p = self.nextpage.next()
        except:
            p = None
        self.mylock.release()
        return p

    def finish(self):
        self.pages.clear()
        #os.remove(self.filename)
        a = file('finish.txt', 'a')
        a.write(self.name)
        a.write('\n')
        a.close()

    def flush(self):
        self.file.flush()


class FinishException(Exception):
    pass


class Ebay:
    threadcount = config.config.threadcount

    def __init__(self, site, cat_id=0):
        self.baseurl = 'http://%s/items/?_ipg=200&_sacat=%s&_pgn=%%s' % (SiteUrl[site], cat_id)
        self.name = '%s_%s' % (site, cat_id)
        self.pages = Pages(self.name)
        self.zeroCount = 0

    def Request(self, PageNumber=1):
        return getPage(self.baseurl % PageNumber)

    def finish(self):
        self.pages.finish()
        a = file('finish.txt', 'a')
        a.write(self.name)
        a.write('\n')
        a.close()

    def StartOne(self, d=None):
        name = threading.currentThread().getName()
        f = file('urls/%s.txt' % name, 'a')
        err = 0
        try:
            pagecount = None
            while mysignal.ALIVE:
                if not d:
                    d = self.pages.next()
                    if d is None or (pagecount and d >= pagecount):
                        raise FinishException
                print "%s : %d" % (self.name, d)
                try:
                    result = self.Request(d)
                except Exception, info:
                    print name, d, info
                    err += 1
                    if err > 5:
                        raise FinishException
                    continue
                else:
                    d, pagecount = self.GetResult(result, d, f)
        except FinishException:
            self.threadcount -= 1
            if self.threadcount == 0:
                self.pages.finish()
        f.close()

    def run(self):
        print self.name, 'start'
        worker = []
        for i in range(self.threadcount):
            h = threading.Thread(target=self.StartOne, name='%s_%d' % (self.name, i))
            h.setDaemon(True)
            h.start()
            worker.append(h)

        while threading.activeCount() > 1 and mysignal.ALIVE:
            try:
                time.sleep(5)
            except:
                pass
        self.pages.flush()
        print self.name, 'finish'

    def getPageCount(self, result):
        try:
            data = COUNTRE.findall(result)
            total = int(NUMRE.sub('', data[0]))
        except:
            return 0
        #if total == 0:
        #    file('a.html', 'w').write(result)
        return (total - 1) / 200 + 1

    def GetResult(self, data, page, f):
        if data is None:
            return page, None
        pagecount = self.getPageCount(data)
        if not pagecount:
            self.zeroCount += 1
            print self.name, pagecount, 'not any found'
            if self.zeroCount > 20:
                raise FinishException
            return page, pagecount
        self.zeroCount = 0
        all = ITEMIDRE.findall(data)

        f.write('\n'.join(all))
        f.write('\n')
        self.pages.add_page(page)

        print '%s %d success %s ' % (self.name, page, pagecount)
        if len(all) < 200:
            raise FinishException

        if pagecount and pagecount <= page:
            raise FinishException
        return None, pagecount


def CategoryFace():
    worker = []
    FINISH = []
    if os.path.exists('finish.txt'):
        for x in file('finish.txt'):
            FINISH.append(x.strip())
    for line in file('category.txt'):
        site, catid = line.strip().split('\t')
        if not mysignal.ALIVE:
            break
        name = '%s_%s' % (site, catid)
        if name in FINISH:
            continue
        try:
            c = Ebay(site, catid)
        except KeyError:
            continue
        c.run()


if __name__ == '__main__':
    CategoryFace()
