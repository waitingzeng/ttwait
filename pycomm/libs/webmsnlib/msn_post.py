#! /usr/bin/env python
#coding=utf-8
import socket
import time
import threading
import json
import httplib
import sys
from pycomm.utils.text import get_in
from msn_live import MSNLive


class LoginFailException(Exception):pass

class BlockPostException(Exception):pass

class EmailErrorException(Exception):pass

class FinishException(Exception):pass
class LimitException(Exception):pass
class HadAddException(Exception):pass
class TooManyException(Exception):pass


class MSNPost(MSNLive):
    def __init__(self, name, psw):
        MSNLive.__init__(self, name, psw)
        self.cid = ''
        self.mailhost = 'mail.live.com'
        self.canary = None

    def get_canary(self, cid):
        if self.canary:
            return self.canary
        url = 'https://profile.live.com/cid-%s/' % cid
        page = self.web.get_page(url)
        if page is None:
            self.log.debug('get %s page fail', url)
            return None
        if page.find('确认是否有查看的权限') != -1:
            self.log.debug('login fail')
            raise LoginFailException
        #file('%s.html' % cid, 'w').write(page)
        if page.find('sn_pp_sm_cnctpost') == -1:
            self.log.debug('can not found sn_pp_sm_cnctpost')
            raise HadAddException
        sn_frInvite = get_in(page, "var sn_frInvite", "</script>")
        if not sn_frInvite:
            self.log.debug('get sn_frInvite fail')
            return None
        canary = get_in(sn_frInvite, '"canary":"', '"')
        if not canary:
            self.log.debug('get canary fail')
            return None
        self.canary = str(eval('u"%s"' % canary))
        return self.canary

    def get_self_canary(self):
        if self.canary:
            return self.canary
        url = 'https://profile.live.com/'
        page = self.get_page(url)
        if page is None:
            self.error('get profile page fail')
            return None
        if page.find('确认是否有查看的权限') != -1:
            self.error('login fail')
            raise LoginFailException
    
        sn_frInvite = get_in(page, "var sn_frInvite", "</script>")
        if not sn_frInvite:
            self.log.debug('get sn_frInvite fail')
            return None
        canary = get_in(sn_frInvite, '"canary":"', '"')
        if not canary:
            self.log.debug('get canary fail')
            return None
        self.canary = str(eval('u"%s"' % canary))
        return canary
    


    def add_friend(self, cid, body = ''):
        canary = self.get_canary(cid)
        if not canary:
            return canary
        url = 'https://profile.live.com/cid-%s/' % cid
        data = {
            'canary' : canary,
            'recipientId' : 'c%s' % cid,
            'personalMessage' : body,
            'isFavorite' : 'false',
            'showProfileUpsell' : 'true',
            'isLimitedFriend' : 'false',
            'isAlreadyFavorite' : 'false',
        }
        postUrl = 'https://profile.live.com/handlers/friendinvite/send.mvc'
        res = self.web.get_page(postUrl, data, headers={'referer' : url})
        if res is None:
            self.log.debug('post add friend(%s) page fail' % cid)
            return None
        if res.find('&#36992;&#35831;&#24050;&#21457;&#36865;') != -1 or res.find('&#23436;&#25104;&#12290;') != -1:
            return True
        if res.find('&#35813;&#30005;&#23376;&#37038;&#20214;&#22320;&#22336;&#19981;&#23384;&#22312;') != -1:
            raise EmailErrorException
        if res.find('&#24403;&#21069;&#20986;&#29616;&#20102;&#38382;&#39064;&#65292;') != -1 or res.find('&#24050;&#28385;&#65281;') != -1:
            raise FinishException
        if res.find('&#26080;&#27861;&#21457;&#36865;') != -1:
            raise LimitException
        if res.find('reached the limit for the number of people') != -1:
            raise TooManyException
        #file('a.html', 'w').write(res)
        return False

    def _parse_contact_list(self, page):
        """
        ControlDataIndex:
{cid:"0",showmenu:"1",menudefault:"2",name:"3",contactid:"4",deccid:"5",address:"6",membername:"7",additionalchickletdata:"8",thirdpartyname:"9",attachmenutobody:"10",placedintable:"11",menucustom:"12",tileitemid:"13",nameitemid:"14",psmitemid:"15",badgeitemid:"16",actiontypeurloverride:"17",childicid:"18"}
        """
        if page is None:
            return []
        if not self.cid:
            self.cid = get_in(page, '"vcid":"', '"')
            self.mailhost = get_in(self.web.url, '//', '/mail/')
        cids = []
        try:
            datatxt = get_in(page, 'window.ic_control_data = ', ';')
            data = json.loads(datatxt)
            #print data
            for i in range(2, 27):
                key = 'ic%x' % i
                if key in data:
                    cids.append([data[key][0], data[key][4], data[key][5], data[key][6], data[key][3]])
                    #if data[key][6]:
                    #    cids.append(data[key][6])
        except Exception, info:
            self.error(info)
            sys.exit()
        return cids

    def get_contact_list(self, filter='', all=True):#filter = Messenger
        baseurl = 'https://%s/mail/ContactMainLight.aspx?ContactsSortBy=FileAs&Page=%s&n=%s'
        if filter:
            baseurl = baseurl + '&CategoryFilter=%s' % filter
        p = 1
        url = baseurl % (self.mailhost, p, time.time())
        page = self.web.get_page(url)
        
        total = get_in(page, '<span class="cnt">&#x200e;(', ')')
        if not total:
            total = '1'
        total = int(total)
        pageNum = (total - 1)/25 + 1
        cids = self._parse_contact_list(page)
        if all:
            threadname = threading.currentThread().getName()
            for p in range(2, pageNum+1):
                self.error('begin get contactlist %s page: %s %s', filter, pageNum, p)
                url = baseurl % (self.mailhost, p, time.time())
                page = self.web.get_page(url)
                cids.extend(self._parse_contact_list(page))
        return cids

    def get_mt(self):
        mt = self.web.get_cookies('mt')
        if mt is None:
            self.get_contact_list(all=False)
            mt = self.web.get_cookies('mt')
            if mt is None:
                return ''
        return mt.value

    def delete_contact(self, cids, trys=5):
        if trys <0:
            return []
        data = {
            '__VIEWSTATE' : '',
            'mt' : self.get_mt(),
            'EmptyFolder' : 'false',
            'EmptyFolderID' : '0',
            'IsForRedirect' : 'false',
            'folderCache' : '',
            'categoriesCache' : '',
            'DestGroupId' : '',
            'ToolbarActionItem' : 'delete_contacts',
            'InfoPaneActionItem' : '',#'delete_contactsConfirmYes',
            'SelectedContacts' : ['%s;%s;False;https://profile.live.com/cid-%s/details/Edit/?break=1&ContactId=%s&ru=;1' % (x[0], x[1], self.cid, x[0]) for x in cids]
        }
        posturl = 'https://%s/mail/ContactMainLight.aspx?ContactsSortBy=FileAs&n=%s' % (self.mailhost, time.time())
        
        data['ToolbarActionItem'] = ''
        data['InfoPaneActionItem'] = 'delete_contactsConfirmYes'
        res = self.web.get_page(posturl, data, muti=True)
        if res is None:
            self.log.debug('delete contact fail, retry %d' % trys)
            return self.delete_contact(cids, trys-1)

        if res.find('联系人已经被删除') != -1:
            return True
        return False

    def del_all(self, remove_datas):
        ct = 0
        for i in xrange(0, len(remove_datas), 25):
            r_cids = [(x[1], x[2]) for x in remove_datas[i:i+25]]
            ct += 25
            if self.delete_contact(r_cids[0:1]):
                self.log.debug('remove success %d', ct)
            else:
                self.log.debug('remove fail %d', ct)
                

    def del_not_email_contacts(self):
        cids = self.get_contact_list()
        removes = [x for x in cids if not x[3]]
        self.del_all(removes)
        return [x[0] for x in removes]

def test():
    from optparse import OptionParser, OptionGroup
    from pycomm.log import open_debug, open_log
    open_log('MSNPOST')
    open_debug()
    parser = OptionParser(conflict_handler='resolve')
    parser.add_option('-f', '--function', dest="function", action='store', type="string", help="the function want to call")
    parser.add_option("-e", "--email", dest="email", action="store", help="the microsoft email", type="string")
    group = OptionGroup(parser, 'add_friend')
    group.add_option("-c", "--cid", dest="cid", action="store",
                        help="the cid", type="string")
    
    options, args = parser.parse_args(sys.argv[1:])
    
    if not options.email or not options.function:
        parser.print_help()
        return
    
    app = MSNPost(options.email, '846266')
    if app._login():
        print 'login success'
        if options.function == 'add_friend':
            if not options.cid:
                parser.print_help()
                return
            print app.add_friend(options.cid)
    else:
        print 'login fail'
    
if __name__ == '__main__':
    test()
