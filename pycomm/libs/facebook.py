#coding=utf8

from pycomm.log import log, open_log, open_debug, PrefixLog
from pycomm.singleweb import SingleWeb
from pycomm.utils import text
try:
    import ujson as json
except ImportError:
    log.trace("can not import ujson")
    import json

import urllib2
import urllib
from pyquery import PyQuery as pq
import random

class FaceBook(object):
    def __init__(self, email, psw, *args, **kwargs):
        self.web = SingleWeb(*args, **kwargs)
        self.log = PrefixLog('FaceBook %s %s' % (email, psw))
        self.email = email
        self.psw = psw
        

    """
    def reg(self, email, psw, lastname=None, firstname=None, ):
        data = {
            'lastname' : lastname or text.rnd_str(5),
            'firstname' : firstname or text.rnd_str(5),
            'reg_email__' : email,
            'reg_email_confirmation__' : email,
            'reg_passwd__' : psw,
            'sex' : ['1'],
            'birthday_year' : ['%s' % (random.uniform(1985, 1995))],
            'birthday_month' : ['%s' % (random.uniform(1, 12))],
            'birthday_day' : ['%s' % random.uniform(1, 28)],

        }
        index_url = 'https://www.facebook.com/index.php?stype=lo&lh=Ac9J1pqgvv2IP73t'
        res_page = self.web.submit_url(index_url, data={'email' : self.email, 'pass' : self.psw}, name='reg')
    """

    def login(self):
        self.log.trace("begin login")
        index_url = 'https://www.facebook.com/index.php?stype=lo&lh=Ac9J1pqgvv2IP73t'
        res_page = self.web.submit_url(index_url, data={'email' : self.email, 'pass' : self.psw}, name='login_form')
        if self.web.url.find('welcome') != -1:
            c_user = self.web.get_cookies('c_user')
            self.uin = c_user.value
            self.log.trace("login success")
            return True
        self.log.trace("login fail")
        return False

    def get_friends_data(self, uin, data):
        if not data:
            return []
        b = 'for (;;);'
        data = data[len(b):]
        file('data.js', 'w').write(data)
        try:
            data = json.loads(data)
            err = data.get('errorDescription', '')
            if err:
                log.error("get data fail %s", err)
                return []
            html = data['domops'][0][3]['__html']
            users_link = [x for x in pq(html).find('a') if pq(x).attr('data-hovercard')]
            items = []
            for link in users_link:
                link = pq(link)
                uin = text.get_in(link.attr('data-hovercard'), 'user.php?id=')
                slug = text.get_in(link.attr('href'), 'http://www.facebook.com/')
                can_be_add = link.parents('._8m').find('.addButton').size() > 0
                item = {'state' : 0, 'uin' : uin, 'slug' : slug, 'name' : link.text(), 'can_be_add' : can_be_add}
                items.append(item)
            return items
        except:
            log.exception("get uins data fail %s", uin)
            return []


    def get_friends(self, uin, start=0):
        url = "http://www.facebook.com/ajax/browser/list/allfriends/?uid=%s&infinitescroll=1&location=friends_tab_tl&start=%s&__user=%s&__a=1" % (uin, start, self.uin)
        log.info('get_friends by url %s', url)
        data = self.web.get_page(url)
        items = self.get_friends_data(uin, data)
        
        return items        
    
    def generate_phstamp(self, qs, dtsg):
        csrf=['1'];

        for i in dtsg:
            csrf.append(str(ord(i)))    
        csrf.append(str(len(qs)))
        return ''.join(csrf)

    def make_post_data(self, data, env):
        data['fb_dtsg'] = env['fb_dtsg']
        data = urllib.urlencode(data)
        data = '%s&phstamp=%s' % (data, self.generate_phstamp(data, env['fb_dtsg']))
        return data
    
    def get_user_env(self, user):
        url = 'http://www.facebook.com/%s' % urllib.quote_plus(user)
        res_page = self.web.get_page(url)
        if not res_page:
            log.debug("get user %s page fail", user)
            return False
        file('debug.html', 'w').write(str(res_page))
        env = text.get_in(res_page, '\nenvFlush(', ');')
        if env:
            try:
                env = json.loads(env)
            except:
                log.debug("get user %s env json loads %s fail", user, env)
                env = None
        if not env:
            log.debug("get user %s env fail", user)
            return False
        return env

    def send_msg(self, uin, user,  msg):
        env = self.get_user_env(user)
        if not env:
            return False

        data = {
            'body'  : msg,
            'action' : 'send',
            'recipients[0]' : uin,
            '__user'  : self.uin,
            '__a' : '1',
        }
        data = self.make_post_data(data, env)
        post_url = 'http://www.facebook.com/ajax/messaging/send.php'
        res_page = self.web.get_page(post_url, data=data)
        if res_page and res_page.find("payload") != -1:
            self.log.debug("send msg to %s success", user)
            return True

        self.log.debug("send msg to %s fail", user)
        return False
        

    def add_friend(self, uin, user):
        
        env = self.get_user_env(user)
        if not env:
            return False

        data = {
            'to_friend' : uin,
            'action' : 'add_friend',
            'how_found' : 'profile_button',
            'ref_param' : '',
            'link_data[gt][profile_owner]' : uin,
            'link_data[gt][ref]timeline' : 'timeline',
            'outgoing_id' : '',
            'logging_location' : '',
            'no_flyout_on_click' : 'true',
            'ego_log_data' : '',
            'http_referer' : '',
            '__user' : self.uin,
            '__a' : '1',
        }
        data = self.make_post_data(data, env)
        post_url = 'http://www.facebook.com/ajax/messaging/send.php'
        res_page = self.web.get_page(post_url, data=data)
        if res_page and res_page.find("payload") != -1:
            self.log.debug("add_friend %s success", user)
            return True

        log.debug("send msg to %s fail", user)
        return False
        

if __name__ == '__main__':
    open_debug()
    app = FaceBook(proxy='127.0.0.1:8087', debug=1)
    if app.login('yuanchang992sheng@hotmail.com', 'TTwait846266'):
        #print app.get_friends('1194038723')
        print app.send_msg('509241535', 'hafrp3', 'http://www.money-so-easy.com')
    else:
        print 'login fail'
