#! /usr/bin/env python
#coding=utf-8
import re
import base64

from pycomm.log import log
from pycomm.utils.text import get_in, get_in_list
from pycomm.utils import mixin
from xml_content import get_xml


oim_maildata_url = 'https://rsi.hotmail.com/rsi/rsi.asmx'
oim_maildata_soap = 'http://www.hotmail.msn.com/ws/2004/09/oim/rsi/GetMetadata'
oim_read_url = 'https://rsi.hotmail.com/rsi/rsi.asmx'
oim_read_soap = 'http://www.hotmail.msn.com/ws/2004/09/oim/rsi/GetMessage'
oim_del_url = 'https://rsi.hotmail.com/rsi/rsi.asmx'
oim_del_soap = 'http://www.hotmail.msn.com/ws/2004/09/oim/rsi/DeleteMessages'

log.debug('import oim')


def send_oim_message(self, msg, to):
    if not to or not msg:
        return
    try:
        self._send("UUM", "%s 1 1 %s\r\n%s" % (to, len(msg), msg), raw=1)
        return True
    except Exception, info:
        log.error('*** %s %s \r\n%s' % (self.user, info, msg))
    return False
mixin.setMixin('msn', 'send_oim_message', send_oim_message)


# <GetMetadataResponse xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi">See #XML_Data</GetMetadataResponse>
oim_maildata_re = re.compile(r'<GetMetadataResponse([^>]*)>(.*)</GetMetadataResponse>')

def get_oim_ticket(self):
    t = get_in(self.tickets.web_ticket, 't=', '&')
    p = get_in(self.tickets.web_ticket, 'p=')
    return t, p
mixin.setMixin('msn', 'get_oim_ticket', get_oim_ticket)


def get_oim_maildata(self):
    t, p = self.get_oim_ticket()
    if not t or not p:
        return []
    
    xml = get_xml('get_oim_maildata', t = t, p = p)

    try:
        data = self.get_page(oim_maildata_url, xml, SOAPAction=oim_maildata_soap)
    except Exception, info:
        log.error('get oim mail url error, code:%s resp:\n%s', info.code, info.fp.read())
        return []
        
    
    if not data:
        log.debug("*** get oim mail data page fail")
        return []
    
    resp = get_in(data, '<GetMetadataResponse', '</GetMetadataResponse>')
    
    msgs = []
    for m in get_in_list(resp, '<M>', '</M>'):
        oim_type = get_in(m, '<T>', '</T>')
        netword = oim_type == '13' and 32 or 1
        
        sender = get_in(m, '<E>', '</E>')
        if not sender:
            continue
        msg_id = get_in(m, '<I>', '</I>')
        if not msg_id:
            continue
        msgs.append(msg_id)
        
    return msgs
    
mixin.setMixin('msn', 'get_oim_maildata', get_oim_maildata)


def get_oim_message(self, msgid):
    t, p = self.get_oim_ticket()
    
    # read OIM
    xml = self.get_xml('get_oim_message', t=t, p=p, msgid=msgid)

    try:
        
        data = self.get_page(oim_read_url, xml, SOAPAction=oim_read_soap)
    except Exception, info:
        log.error("get oim message error code:%s, resp:\n%s", info.code, info.fp.read())
        return False
        
    if not data:
        log.debug("*** get oim message data page fail")
        return False
    
    # why can't use preg_match('#<GetMessageResult>(.*)</GetMessageResult>#', $data, $matches)?
    # multi-lines?
    for message in get_in_list(data, '<GetMessageResult>', '</GetMessageResult>'):
        lines = message.split('\n')
        header = True
        ignore = False
        s_oim = []
        for line in lines:
            line = line.rstrip()
            if header:
                if not line:
                    header = False
                continue
            if not line:
                break
            s_oim.append(line)
    
    msg = base64.b64decode(''.join(s_oim))
    
    log.debug('*** we get oim %s:%s', msgid, msg)
    
    if not self.del_oim_message(msgid):
        log.debug("Can't delete OIM: %s", msgid)
    else:
        log.debug("delete oim %s success", msgid)
    
    return msg
mixin.setMixin('msn', 'get_oim_message', get_oim_message)

def del_oim_message(self, msgid):
    t, p = self.get_oim_ticket()
    # delete OIM
    xml = get_xml('del_oim_message', t=t, p=p, msgid=msgid)
    try:
        data = self.get_page(oim_del_url, xml, SOAPAction=oim_del_soap)
    except Exception, info:
        log.error("del oim message error, code:%s, resp:%s", info.code, info.fp.read())
        return False
    
    if not data:
        return False
    else:
        return True
mixin.setMixin('msn', 'del_oim_message', del_oim_message)