#! /usr/bin/env python
#coding=utf-8
import os
import os.path as osp
from random import choice
import threading
import json
import traceback
import time
from pycomm.log import log
from pycomm.singleweb import get_page
from pycomm.utils.text import rnd_str
from pycomm.libs.google.api import Api


def _shortcut(url, *args, **kwargs):
    try:
        api = Api('AIzaSyDRPL5alBt_dQ-1IZElkoI19aUm_85Z0eE')
        return api.url_shortener(url, *args, **kwargs)
    except:
        log.exception("_shortcut fail")
        return ''


def shortcut(url, *args, **kwargs):
    url = '%s?%s' % (url, time.time())
    for i in range(3):
        s = _shortcut(url, *args, **kwargs)
        if s.startswith('http://goo.gl/'):
            log.trace("url %s get short %s", url, s)
            return s
        else:
            log.exception("google shortcut %s fail", url)
            time.sleep(3)

message_map = {
    'cww': 'money-so-easy.com',
    'zuai': 'muchmuchgiveyou.com',
    'pfbag': 'make-money-article.com',
    'diy': 'customdiydropshipping.com',
}


class MessageUrlCache(object):
    LIMIT = 100000
    MSGSDIR = 'msgs'
    MSGPREFIX = ''
    URLLIMIT = 5

    def __init__(self, name='', from_url=None, from_site=None, to_site=None, short_url=False, api_key=None, urllimit=5, **kwargs):
        if not from_site:
            raise Exception("Message Site Not Exists")
        self.log = log
        self.name = name
        self.from_site = from_site
        if not from_url:
            self.from_url = '%s/urls.php?limit=5' % self.from_site
        else:
            self.from_url = from_url

        self.to_site = to_site
        self.api_key = None
        self.short_url = short_url

        self.msgs = []
        self.urls = []
        self.urls_msgs = []

        self.ct = 0
        self.lock = threading.RLock()

        if not osp.exists(self.MSGSDIR):
            os.makedirs(self.MSGSDIR)

    def load_urls(self):
        if self.urls:
            return self.urls
        for i in range(10):
            time.sleep(1)
            self.log.error('get from %s retry %d', self.from_url, i)
            try:
                page = get_page('http://' + self.from_url)
                data = json.loads(page)
                self.log.error('get from %s retry %d success', self.from_url, i)
                self.urls = data
                return data
            except Exception, info:
                self.log.exception("load %s fail", self.from_url)
                continue

        raise info

    def load(self):
        return
        self.clear_msgs_file()
        msgs = []
        urls_msgs = []
        try:
            data = self.load_urls()
        except:
            return msgs

        for i, item in enumerate(data):
            url = item['url']
            if self.to_site:
                url = url.replace(self.from_site, self.to_site)
            url = url.lower()

            #item['url'] = ''.join(choice([x, x.upper()]) for x in url)
            item['url'] = url

            if self.short_url:
                short = shortcut(item['url'], self.api_key)
                if short:
                    item['change_url'] = short
            else:
                if url.find('appspot.com') != -1 and url.find('{time}.') == -1:
                    url = url.replace('http://', 'http://{time}.')
                    item['change_url'] = url
                urls_msgs.append(url)

            msg = '%s\n%s' % (item['title'], item['change_url'])
            msgs.append(msg)
            try:
                file('%s/%s_%s%s.html' % (self.MSGSDIR, self.short_url and 's' or 'r', self.MSGPREFIX, i), 'w').write(msg.encode('utf-8'))
            except:
                pass

        if msgs:
            self.msgs = msgs
            self.urls_msgs = urls_msgs
        else:
            raise Exception("Message Site Not Exists")

        return msgs

    def clear_msgs_file(self):
        prefix = self.short_url and 's_' or 'r_'
        prefix += self.MSGPREFIX
        for f in os.listdir(self.MSGSDIR):
            if not f.startswith(prefix):
                continue
            os.unlink(osp.join(self.MSGSDIR, f))

    def reload(self):
        if self.ct < 100:
            return
        log.error("force reload message cache %s", self.from_site)
        try:
            if self.load():
                self.ct = 0
        except:
            self.LIMIT += self.LIMIT
            pass

    def get(self):
        with self.lock:
            self.ct += 1
            cur_time = int(time.time())
            return '%s.%s' % (cur_time, message_map.get(self.name, message_map.get('cww')))
            #if self.ct >= self.LIMIT:
            #    self.reload()
            #return "Money So Easy \n http://www.bing.com/search?q=money+so+easy"
            return choice(self.msgs).replace('{time}', str(int(time.time() * 1000)))

    def __str__(self):
        return '\n\n'.join(self.oig_msgs)

    def __len__(self):
        return len(self.msgs)


class MuchMessageCache(object):
    def __init__(self, site_config, names, short_url=False, log=log):
        self.msgs = []
        site_config = site_config.dict()
        self.log = log
        for name in names:
            try:
                config = site_config[name]
                config['short_url'] = short_url
                config['name'] = name
                config['log'] = log
                cls = MessageUrlCache(**config)
                self.msgs.append(cls)
            except:
                raise
            cls.MSGPREFIX = '%s_' % name
        self.ct = 0
        self.num = len(self.msgs)
        self.total = []
        self.load()

    def load(self):
        for cls in self.msgs:
            cls.load()

    def reload(self):
        for cls in self.msgs:
            cls.reload()

    def get(self):
        self.ct += 1
        return choice(self.msgs).get()

    def __str__(self):
        return '\n\n'.join(str(x) for x in self.msgs)

    def __getattr__(self, name):
        for msg in self.msgs:
            if msg.name == name:
                return msg
        raise AttributeError

    def __getitem__(self, name):
        return getattr(self, name)

    def __contains__(self, name):
        return bool(getattr(self, name, False))

    def __iter__(self):
        return iter(self.msgs)

if __name__ == '__main__':
    config = {'from_site': 'mainsite.sinaapp.com/cwj', 'name': 'zuai', 'urllimit': 5, 'short_url': False, 'api_key': 'AIzaSyD7ekwAwSUeYkDpcjJtPAVe-gY9Ysy0dUk', 'to_site': 'enjoy-make-money.appspot.com'}

    app = MessageUrlCache(**config)
    app.load()
    print app.get()
