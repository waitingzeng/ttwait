#coding=utf-8
import poplib
import email
import base64

class EmailMsg(object):
    def __init__(self, msg):
        self.msg = msg
        self.subject = self.title = email.Header.decode_header(msg['subject'])[0][0]
        
    
    def get_payload(self, msg=None):
        if msg is None:
            msg = self.msg
        payload = {}
        if msg.is_multipart():
            for part in msg.get_payload():
                payload.update(self.get_payload( part ))
        else:
            types = msg.get_content_type()
            filename = msg.get_filename()
            if types=='application/octet-stream' or types == 'application/zip':
                try:
                   body = base64.decodestring(msg.get_payload())
                   payload[filename]= body
                except:
                   print '[*001*]BLANK'
        return payload


class POP3(object):
    def __init__(self, user, psw, host, port=None, ssl=False, uiddb={}):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.user = user
        self.psw = psw
        self.uids = uiddb
        self.connect()
    
    def connect(self):
        if self.ssl:
            self.pop = poplib.POP3_SSL(self.host, self.port)
        else:
            self.pop = poplib.POP3(self.host)
        self.pop.user(self.user)
        self.pop.pass_(self.psw)
    
    
    def get_new_msgs(self):
        
        uids = self.pop.uidl()[1]
        for item in uids:
            msg_id, uid = item.split()
            if uid not in self.uids :
                yield msg_id, uid
    
    def get_msg(self, msg_id, uid):
        content = self.pop.retr(msg_id)
        self.uids[uid] = msg_id
        msg = email.message_from_string('\n'.join(content[1]))
        
        return EmailMsg(msg)
    
    def get_stat_msgs(self, delete=False):
        ct, size = self.pop.stat()

        for i in range(1, ct+1):
            hdr, messages, octet= self.pop.retr(i)
            mail=email.message_from_string('\n'.join(messages))
            yield EmailMsg(mail)
            if delete:
                self.pop.dele(i)

    def __del__(self):
        self.pop.quit()
