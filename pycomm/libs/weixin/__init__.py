#! /usr/bin/env python
#coding=utf-8
import urlparse
import json
import urllib
import sys
from threading import Thread
import time
from socket import timeout
import httplib
from pycomm.log import log
from pycomm.singleweb import SingleWeb
from pycomm.utils.storage import Storage
TOKEN_EXPIRED = 7200

class GrantType(object):
    client_credential = 'client_credential'

class MediaType(object):
    image = 'image'
    voice = 'voice'
    video = 'video'
    thumb = 'thumb'

class RequestFormat(object):
    JSON = '.json'
    XML = '.xml'

class MessageType(object):
    text = 'text'
    image = 'image'
    voice = 'voice'
    video = 'video'
    link  = 'link'
    card  = 'card'
    subscribe = 'subscribe'
    
    
class AuthFailException(Exception):
    def __init__(self, appid, secret):
        self.appid = appid
        self.secret = secret
    
class WeixinBasicApi(object):
    HOST = 'https://api.weixin.qq.com'
    FORMAT = ''
    def __init__(self, host=None):
        self.web = SingleWeb()
        if host: 
			self.HOST = host
    
    def get_url(self, api, id=None):
        api = api.replace('__', '/')
        if not id:
            api = '/%s%s' % (api, self.FORMAT)
        else:
            api = '/%s/%s%s' % (api, id, self.FORMAT)
        url = urlparse.urljoin(self.HOST, api)
        log.debug('call url %s', url)
        return url
    
    def call(self, data=None, id=None, muti=False, direct_ret = False, headers={}):

        if not data:
            data = {}
        call_frame = sys._getframe(1)
        call_name = call_frame.f_code.co_name
        method, api = call_name.split('_', 1)
        url = self.get_url(api, id)
        
        if call_name != 'get_token':
            data['access_token'] = self.get_token()
        
        if method == 'get':
            url = '%s?%s' % (url, urllib.urlencode(data))
            data = None
        log.debug('%s %s', url, data) 
        res = self.web.get_page(url, data, muti=muti, headers=headers)
        log.info("response data %s", res)
        if direct_ret:
            return res
        return self.parse_res(url, res)
    
    def parse_res(self, url, res):
        if not res:
            return None
        if not self.FORMAT or self.FORMAT == RequestFormat.JSON:
            res = json.loads(res)
        else:
            res = {}
        real_res = {}
        real_res['content'] = res
        if res.get('error', None):
            log.error('url %s had error: %d', url, res['error']['code'])
            real_res['error'] = res['error']['code']
        else:
            real_res['error'] = 0
        return Storage(real_res)
        
    def get_token(self):
        raise NotImplementedError
        
    def post_media(self, fileobj, media_type, thumb_media_id=None):
        data = {
            'type' : media_type,
            'media' : fileobj,
        }
        if thumb_media_id:
            data['thumb_media_id'] = thumb_media_id
        
        res = self.call(data, muti=True)
        
        return res
        
    def get_media(self, media_id):
        res = self.call(id=media_id, direct_ret=True)
        return res
    
    def post_image(self, fileobj):
        return self.post_media( fileobj, MediaType.image )

    def post_voice(self, fileobj):
        return self.post_media( fileobj, MediaType.voice )

    def post_video(self, videofileobj, thumbfileobj):
        res = self.post_media( thumbfileobj, MediaType.thumb )
        if res and res.media_id:
            return self.post_media( videofileobj, MediaType.video, res.media_id )
        else:
            print "post_video->post_image for thumb fail: ",res     


class TimelineApi(WeixinBasicApi):
    def timeline_post():
        pass


class StreamHandler(object):
    def __init__(self):
        pass

    def on_data(self, data):
        log.info('on data %s', repr(data))
        data = data.strip()
        try:
            if not data:
                return
            message = json.loads(data)
        except Exception, e:
            log.exception('exception data is: %s, e %s', data, e)
            return
        if isinstance(message, dict):
            self.on_message(Storage(message))

    def on_message(self, message):
        """ call this if new message comes
        """
        raise NotImplementedError

    def on_error(self, code):
        """ call this if error occurs
        """
        raise NotImplementedError

class MessageApi(WeixinBasicApi, StreamHandler):
    GRANT_TYPE = GrantType.client_credential
    
    def __init__(self, appid, secret, host=None):
        WeixinBasicApi.__init__(self, host)
        StreamHandler.__init__(self)
        self.appid = appid
        self.secret = secret
        self.expires_in = 0
        self.access_token = None
        self.get_token()
    
    def get_token(self):
        if self.access_token and self.expires_in >= int(time.time()):
            return self.access_token
        
        data = {
            'appid' : self.appid, 
            'secret' : self.secret,
            'grant_type' : self.GRANT_TYPE
        }
        res = self.call(data)

        if res['error'] != 0:
            raise AuthFailException(self.appid, self.secret)
        
        self.expires_in = int(time.time()) + res['content']['expires_in']
        self.access_token = res['content']['access_token']
        log.info('get access_token %s', self.access_token)
        return self.access_token
    
    def get_help__configuration(self):
        res = self.call()
        return res
    
    def get_users(self, username):
        res = self.call(id=username)
        return res
    
    def post_messages(self, content, media=None, msginfo=None, thumb_media_id=None, title=None, description=None, url=None, msg_type=None, msg_json=None):
        if media:
            type = media.type
        elif msginfo and msginfo['msg_text_type']:
            type = msginfo['msg_text_type']
        else:
            type = MessageType.text
        if msg_type:
            type = msg_type
        headers = {}
        if msg_json:
            type = 'news'
            headers['Content-Type'] = 'application/json'
            data = msg_json
        else:    
            data = {
                'type' : type,
                'content' : content,
                'media_id' : media and media.media_id or '',
                'weixin_id' : msginfo and msginfo['sharecard_username'] or '',
                'thumb_media_id' : thumb_media_id or '',
                'title' : title or '',
                'description' : description or '',
                'url' : url or ''
            }
        res = self.call(data, headers=headers)
        return res
            
    def post_messages__send(self, message_id, to_users=[]):
        if not isinstance(to_users, (list, tuple)):
            to_users = [to_users]
        data = {
            'to_users' : ','.join(to_users)
        }
        res = self.call(data, id=message_id)
        return res
    
    def post_messages__send_all(self, message_id):
        res = self.call(id=message_id)
        return res
    
    def send_message(self, content, to_users=[]):
        message = self.post_messages(content)
        message_id = message['content']['message_id']
        ret = 0
        if message_id > 0:
            ret = self.post_messages__send(message_id, to_users)
        return ret

    def get_messages(self, message_id=None, limit=0, since_id=0):
        if message_id:
            res = self.call(id=message_id)
        else:
            
            data = {
                'limit' : str(limit),
                'since_id' : str(since_id)
            }
            res = self.call(data)
        return res


    def handle_message(self, **options):
        async = options.pop('async', False)
        handler = options.pop('handler', None)
        if not handler:
            handler = self
        self._stream = Stream(self.get_token(), handler, **options)
        self._stream.messages(async)
        
    def on_message(self, message):
        log.trace('on message %s', message)




class Stream(object):
    HOST = 'stream.weixin.qq.com'
    def __init__(self, access_token, handler, **options):
        self._access_token = access_token
        self._handler = handler
        self._running = False
        self._timeout = options.get("timeout", 305.0)
        self._retry_count = options.get("retry_count")
        self._retry_time = options.get("retry_time", 10.0)
        self._snooze_time = options.get("snooze_time",  5.0)
        self._buffer_size = options.get("buffer_size",  15)

    def _run(self):
        self._url = "/messages?access_token=%s" % self._access_token

        # Connect and process the stream
        error_counter = 0
        conn = None
        exception = None
        while self._running:
            if self._retry_count is not None and error_counter > self._retry_count:
                # quit if error count greater than retry count
                break
            try:
                conn = httplib.HTTPSConnection(self.HOST)
                conn.connect()
                conn.sock.settimeout(self._timeout)
                conn.request('GET', self._url)
                resp = conn.getresponse()
                if resp.status != 200:
                    if self._handler.on_error(resp.status) is False:
                        break
                    error_counter += 1
                    log.error('on error %s', error_counter)
                    time.sleep(self._retry_time)
                else:
                    error_counter = 0
                    self._read_loop(resp.fp)
            except timeout:
                if self._handler.on_timeout() == False:
                    break
                if self._running is False:
                    break
                conn.close()
                time.sleep(self._snooze_time)
            except Exception, exception:
                # any other exception is fatal, so kill loop
                break

        # cleanup
        self._running = False
        if conn:
            conn.close()

        if exception:
            raise

    def _read_loop(self, sock):
        log.info('connect stream success')
        while self._running:
            chunk = sock.readline()
            if chunk == '':
                self._running = False
                break

            for line in chunk.split('\n'):
                self._handler.on_data(line)
                

        self.on_closed()


    def _start(self, async):
        self._running = True
        if async:
            Thread(target=self._run).start()
        else:
            self._run()

    def on_closed(self):
        """Called when the response has been closed by Wechat
        """
        pass

    def messages(self, async=False):
        if self._running:
            raise Exception('Stream object already connected!')
        self._start(async)

    def disconnect(self):
        if self._running is False:
            return
        self._running = False

def test():
    import sys
    from optparse import OptionParser
    from pycomm.log import open_log, open_debug

    open_debug()
    parser = OptionParser(conflict_handler='resolve')
    parser.add_option('--appid', dest='appid',  action="store", type="string")
    parser.add_option('--appkey', dest='appkey', action="store", type="string")
    parser.add_option('--sendto', dest="sendto", action="append", type="string")
    parser.add_option('--getuser', dest="getuser", action="store", type="string")
    parser.add_option('--msg', dest="msg", action="store", type="string")


    options, args = parser.parse_args(sys.argv[1:])

    if not options.appid:
        options.appid = 'wx91a0600805ba2d08'
        options.appkey = '3854900ed2583c8abb7287a7d6ba5edf'

    app = MessageApi(options.appid, options.appkey)

    if options.getuser:
        print app.get_users(options.getuser)
        return

    if options.sendto:
        print app.send_message(options.msg, options.sendto)
    else:
        app.handle_message()


if __name__ == '__main__':
    test()








