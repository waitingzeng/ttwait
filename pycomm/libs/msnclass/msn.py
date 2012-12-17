#! /usr/bin/env python
#coding=utf-8
import uuid
import re
import socket
import threading
import time
import traceback
import sys
import os

from pycomm.utils.html import htmlspecialchars
from pycomm.utils.tracktime import DiffTime
from pycomm.log import log
from pycomm.utils import mixin
from utils import encode, decode, get_page
from mbi import encrypt
from xml_content import get_xml
from sso import get_tickets
from message import get_message

from challenge import _msn_challenge, PRODUCT_ID


import oim
import contact
socket.setdefaulttimeout(30)
Headers = {'Content-Type': 'application/soap+xml; charset=utf-8; action=""'}
class TimeoutException(Exception):
    pass

class ServerErrorException(Exception):
    def __init__(self, code, error):
        self.code = code
        self.error = error
   
    def __str__(self):
        return self.error


class MSN(mixin.Mixin):
    __mixinname__ = 'msn'
    
    server = 'messenger.hotmail.com'
    port = 1863

    passport_url = 'https://login.live.com/RST.srf'

    protocol = 'MSNP18'
    
    login_method = 'SSO'
    #application_id = 'CFE80F9D-180F-4399-82AB-413F33A1FA11'
    application_id = '3794391A-4816-4BAC-B34B-6EC7FB5046C6'
    machine_guid = '{661896D6-FA40-46C9-88F1-C512CD5CA875}'
    #machine_guid = '{6374cf40-0760-11e1-ace3-005056c00008}'

    slang = '0x0409'
    osname = 'winnt'
    osver = '6.1.1'
    osplatform = 'i386'
    clientname = 'MSMSGS'
    clientver = '14.0.8117.416'
    

    def __init__(self, wait_chl=True):
        self.initmixin()
        
        self.fd = False
        self.error = ''

        self.authed = False
        self.user = ''
        self.password = ''
        
        self.tickets = None

        # generate GUID
        self.machine_guid = '{%s}' % uuid.uuid4()
        
        self.error_code = 0
        self.last_code = None
        
        self.callbacks = []

        self.wait_chl = wait_chl
        #self.application_id = uuid.uuid4()
        #self.machine_guid = '{%s}' % uuid.uuid4()
        
    def add_error_callback(self, func):
        self.callbacks.append(func)

    def get_xml(self, name, **kwargs):
        for k,v in kwargs.items():
            kwargs[k] = htmlspecialchars(v)
            
        kwargs.setdefault('application_id', self.application_id)
        kwargs.setdefault('passport_policy', self.passport_policy)
        
        if self.tickets:
            for k, v in self.tickets.items():
                kwargs.setdefault(k, htmlspecialchars(v))
        
        return get_xml(name, **kwargs)

    def get_page(self, url, data, **kwargs):
        kwargs.update({
            'Content-Type' : 'text/xml; charset=utf-8',
            #'User-Agent' :  'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; Messenger %s)' % self.clientver
            'User-Agent' : 'MSN Explorer/9.0 (MSN 8.0; TmstmpExt)',
        })
        log.debug("*** URL: %s" % url)
        
        self.last_code, data = get_page(url, data, kwargs)
        return data        

    def get_passport_ticket(self, url = ''):
        
        if not url:
            passport_url = self.passport_url
        else:
            passport_url = url

        xml = self.get_xml('passport_ticket', user=self.user, password=self.password, passport_url=passport_url)

        data = self.get_page(passport_url, xml)
                
        if not data:
            log.debug("*** %s get passport ticket failed", self.user)
            return []
        
        if data.find('<faultcode>psf:Redirect</faultcode>') != -1 :
            matches = re.search(r"<psf\:redirectUrl>(.*)</psf\:redirectUrl>", data)
            if matches:
                redirect_url = matches.group(1)
                if redirect_url == passport_url:
                    log.debug("*** redirect, but redirect to same URL!")
                    return False
                
                log.debug("*** redirect to %s" % redirect_url)
                return self.get_passport_ticket(redirect_url)
        
        self.tickets = get_tickets(data)
        return self.tickets

    

    def connect(self, user, password, redirect_server = '', redirect_port = 1863, timeout = 60):
        self.tid = 1
        if not redirect_server:
            try:
                self.fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.fd.connect((self.server, self.port))
            except Exception, info:
                self.error = "Can't connect to %s:%s, error => %s" % (self.server, self.port, info)
                return False
            
        else:
            try:
                self.fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.fd.connect((redirect_server, redirect_port))
            except Exception, info:
                self.error = "Can't connect to %(redirect_server)s:%(redirect_port)s, error => %(info)s" % locals()
                return False
            
        #stream_set_timeout(self.fp, self.stream_timeout)
        self.authed = False
        # NS: >>> VER {id} MSNP18 CVR0
        self._send("VER", "%s CVR0" % self.protocol)
        timestamp = time.time()

        while self.fd:
            if (time.time() - timestamp) > timeout:
                raise TimeoutException
            try:
                code, tid, params = self._recv()
            except:
                if self.authed:
                    time.sleep(1)
                    log.trace('%s recv error', user)
                    continue
                self.disconnect()
                return False
            
            if code == 'VER':
                # NS: <<< VER {id} MSNP18 CVR0
                # NS: >>> CVR {id} 0x0409 winnt 5.1.3 i386 MSMSGS 14.0.8117.416 msmsgs {user}
                self._send("CVR", "0x040c winnt 5.1 i386 %s %s msmsgs %s" % (self.clientname, self.clientver, user))
                continue

            elif code == 'CVR':
                # NS: <<< CVR {id} {ver_list} {download_serve} ....
                # NS: >>> USR {id} SSO I {user}
                self._send("USR",  "%s I %s" % (self.login_method, user))
                continue

            elif code == 'USR':
                # already login for passport site, finish the login process now.
                # NS: <<< USR {id} OK {user} {verify} 0
                if self.authed:
                    #self.start()
                    self._send("CHG", "NLN")
                    if self.wait_chl:
                        continue
                    else:
                        return True

                # max. 16 digits for password
                if len(password) > 16:
                    password = password[:16]

                self.user = user
                self.password = password

                # NS: <<< USR {id} SSO S {policy} {nonce}
                
                SSO, S, policy, nonce = params.split(' ')
                #@list(/* USR */, /* id */, /* SSO */, /* S */, $policy, $nonce,) = @explode(' ', $data)

                self.passport_policy = policy
                self.get_passport_ticket()
                if not self.tickets:
                    # logout now
                    # NS: >>> OUT
                    self.disconnect()
                    self.error = 'Passport authenticated fail!'
                    log.debug("*** %s" % self.error)
                    return False

                login_code = encrypt(self.tickets.secret, nonce)

                # NS: >>> USR {id} SSO S {ticket} {login_code} {machine_guid}
                self._send("USR", "%s S %s %s %s" % (self.login_method, self.tickets.ticket, login_code, self.machine_guid))

                self.authed = True
                continue

            elif code == 'XFR':
                # main login server will redirect to anther NS after USR command
                # NS: <<< XFR {id} NS {server} U D
                t = params.split(' ')
                ip, port = t[1].split(':')
                port = int(port)
                
                #@list(/* XFR */, /* id */, /* NS */, $server, /* ... */) = @explode(' ', $data)
                #@list($ip, $port) = @explode(':', $server)
                # this connection will close after XFR
                self.disconnect()

                try:
                    self.fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.fd.connect((ip, port))
                    
                except:
                    self.error = "Can't connect to %s:%s, error" % (ip, port)
                    log.debug("*** %s" % self.error)
                    return False
                
                # reset trans id
                self.tid = 1

                #stream_set_timeout(self.fp, self.stream_timeout)
                # NS: >>> VER {id} MSNP18 CVR0
                self._send("VER", "%s CVR0" % self.protocol)
                continue

            elif code == 'GCF':
                # return some policy data after 'USR {id} SSO I {user}' command
                # NS: <<< GCF 0 {size}
                mlen = int(params.split()[-1])
                #@list(/* GCF */, /* 0 */, $size,) = @explode(' ', $data)
                # we don't need the data, just read it and drop
                self._recvmsg(mlen)
                continue
            elif code == 'CHG':
                continue
            elif code == 'CHL':
                # randomly, we'll get challenge from server
                # NS: <<< CHL 0 {code}
                chl_code = params.split()[-1]

                fingerprint = _msn_challenge(chl_code)

                out = "%s 32\r\n%s" % (PRODUCT_ID, fingerprint)
                self._send("QRY", out, raw=1)
                continue
            elif code == 'QRY':
                return True
            else:
                # we'll quit if got any error
                if code.isdigit():
                    # logout now
                    # NS: >>> OUT
                    self.disconnect()
                    self.error = '%s *** error code %s, error text %s' % (self.user, code, params)
                    log.error("NS: %s", self.error)
                    self.error_code = int(code)
                    return False
                
                # unknown response from server, just ignore it
                continue
        # never goto here
                
    def send_oim_message(self, msg, to):
        if not to or not msg:
            return
        try:
            self._send("UUM", "%s 1 1 %s\r\n%s" % (to, len(msg), msg), raw=1)
            return True
        except Exception, info:
            log.error('*** %s send to %s %s \r\n%s' % (self.user, to, info, msg))
        return False
    
    def start(self):
        h = threading.Thread(target=self.main_loop)
        h.setDaemon(True)
        h.start()

    def main_loop(self):
        # since 2009/07/21, no more SBS after USR, so we just do the following step here
        t = DiffTime()
        self._send("PNG")
        while self.fd:
            try:
                code, tid, params = self._recv()
            except:
                if t.get_diff() < 1000:
                    time.sleep(3)
                    try:
                        t.reset()
                    except:
                        pass
                    continue
            self._send("PNG")
            time.sleep(2)
        log.debug("%s main loop out", self.user)
        return 0

    def get_tid(self):
        "Returns a valid tid as string"
        self.tid = self.tid + 1
        return str(self.tid - 1)

    def _send(self, cmd, params = '', raw = 0):
        """Sends a command to the server, building it first as a
        string; uses, if specified, the pseudo fd (it can be either
        msnd or sbd)."""
        tid = self.get_tid()
        fd = self.fd
        if cmd == 'PNG':
            c = cmd + '\r\n'
        else:
            c = cmd + ' ' + tid
        if params: 
            c = c + ' ' + params
        if not raw:
            log.debug(str(fd.fileno()) + ' >>> ' + c)
            c = c + '\r\n'
        c = encode(c)
        return fd.send(c)


    def _recv(self):
        "Reads a command from the server, returns (cmd, tid, params)"
        fd = self.fd
        # cheap and dirty readline, FIXME
        buf = ''
        c = fd.recv(1)
        while c != '\n' and c != '':
            buf = buf + c
            c = fd.recv(1)

        if c == '':
            raise Exception('SocketError')

        buf = buf.strip()
        pbuf = buf.split(' ')

        cmd = pbuf[0]

        # it's possible that we don't have any params (errors being
        # the most common) so we cover our backs
        if len(pbuf) >= 3:
            tid = pbuf[1]
            params = decode(' '.join(pbuf[2:]))
        elif len(pbuf) == 2:
            tid = pbuf[1]
            params = ''
        else:
            tid = '0'
            params = ''

        log.debug(str(fd.fileno()) + ' <<< ' + buf)
        return (cmd, tid, params)


    def _recvmsg(self, msglen):
        "Read a message from the server, returns it"
        fd = self.fd
        left = msglen
        buf = ''
        while len(buf) != msglen:
            c = fd.recv(left)
            #log.debug(str(fd.fileno()) + ' <<< ' + buf)
            buf = buf + c
            left = left - len(c)

        return decode(buf)

    def disconnect(self):
        "Disconnect from the server"
        try:
            self.fd.send('OUT\r\n')
            self.fd.close()
        except:
            pass
        self.fd = None
    

    def __del__(self):
        self.disconnect()

def main():
    from pycomm.log import open_log, open_debug
    from optparse import OptionParser, OptionGroup
    open_log('MSNCLASS', 10)
    open_debug()
    parser = OptionParser(conflict_handler='resolve')
    parser.add_option("-e", "--email", dest="email", action="store", help="the microsoft email", type="string")
    parser.add_option("-p", "--passwd", dest="passwd", action="store", help="the passwd", type="string")
    parser.add_option("-s", "--sendall", dest="sendall", action="store_true", help="sendall")
    parser.add_option("-m", "--members", dest="members", action="store_true", help="get all members")
    parser.add_option("-a", "--addfriend", dest="addfriend", action="store", help="which email to add friend", type="string")
    
    options, args = parser.parse_args(sys.argv[1:])
    
    if not options.email:
        parser.print_help()
        return
    app = MSN(False)

    res = app.connect(options.email, options.passwd or '846266')
    if res:
        log.trace('%s login success', options.email)
        if options.members:
            members = app.get_allow_email()
            print members
        if options.sendall:
            #app.start()
            members = app.get_allow_email()
            for ct, member in enumerate(members):
                msg = get_message('%s hello' % ct)
                #app.send_oim_message(msg, member)
                app.send_oim_message(msg, 'zqc160@163.com')
                log.trace('sendmsg %s %s', ct, member)
                time.sleep(0.2)
        
        if options.addfriend:
            abcontact = app.get_full_addressbook()
            contact = abcontact.find_contact(options.addfriend)

            if contact:
                ret = app.del_contact(contact)
                log.trace("%s exists remove it ret %s", options.addfriend, ret)
            ret = app.add_contact(options.addfriend, 1, "http://www.money-so-easy.com")
            log.trace("add contact %s ret %s", options.addfriend, ret)

    else:
        log.trace('%s login fail', options.email)
        

if __name__ == '__main__':
    main()
