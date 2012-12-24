import urllib2
import urllib
import traceback
import gzip
from StringIO import StringIO
import ClientForm
from ClientForm import ParseFile, ControlNotFoundError, ListControl
LG_DEBUG = True
import httplib
import socket
import time
from multipartposthandler import MultipartPostHandler
from pycomm.log import log
#socket.setdefaulttimeout(30)

HEADERS = {
    'User-Agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1.7) Gecko/20091221 Firefox/3.5.7 GTB6',
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language' : 'zh-cn,zh;q=0.5',
    'Accept-Encoding': 'gzip',
    'Accept-Charset' : 'GB2312,utf-8;q=0.7,*;q=0.7',
    'Keep-Alive' : '300',
    'Connection' : 'keep-alive',
    'Cache-Control' : 'max-age=0',

}

class HTTPRefreshProcessor(urllib2.BaseHandler):
    """Perform HTTP Refresh redirections.

    Note that if a non-200 HTTP code has occurred (for example, a 30x
    redirect), this processor will do nothing.

    By default, only zero-time Refresh headers are redirected.  Use the
    max_time attribute / constructor argument to allow Refresh with longer
    pauses.  Use the honor_time attribute / constructor argument to control
    whether the requested pause is honoured (with a time.sleep()) or
    skipped in favour of immediate redirection.

    Public attributes:

    max_time: see above
    honor_time: see above

    """
    handler_order = 1000

    def __init__(self, max_time=0, honor_time=True):
        self.max_time = max_time
        self.honor_time = honor_time

    def http_response(self, request, response):
        code, msg, hdrs = response.code, response.msg, response.info()
        if code == 200 and hdrs.has_key("refresh"):
            refresh = hdrs.getheaders("refresh")[0]
            ii = refresh.find(";")
            if ii != -1:
                pause, newurl_spec = float(refresh[:ii]), refresh[ii+1:]
                jj = newurl_spec.find("=")
                if jj != -1:
                    key, newurl = newurl_spec[:jj], newurl_spec[jj+1:]
                if key.strip().lower() != "url":
                    return response
            else:
                pause, newurl = float(refresh), response.geturl()
            if (self.max_time is None) or (pause <= self.max_time):
                if pause > 1E-3 and self.honor_time:
                    time.sleep(pause)
                hdrs["location"] = newurl
                # hardcoded http is NOT a bug
                response = self.parent.error(
                    "http", request, response,
                    "refresh", msg, hdrs)

        return response

    https_response = http_response


def get_page(url, data=None, headers={}, times=3, proxy=None, debug=0):
    web = SingleWeb(proxy=proxy, debug=debug)
    req = web.make_req(url, data, headers)
    for i in range(times):
        data = web.get_page(req)
        if data:
            return data
    return None

def proxy(config):
    import socks
    if config.sock.open:
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, config.sock.host, config.sock.port)
        socket.socket = socks.socksocket


class SingleWeb(object):
    no_redirect = False
    def __init__(self, simple=False, proxy=None, cookiejar=None, debug=0):
        self.retry = 0
        self.req = None
        self.resp = None
        self.debug = debug
        h = urllib2.HTTPHandler(debuglevel = debug) 
        self.opener = urllib2.build_opener(h)
        if proxy:
            l_proxy_support = urllib2.ProxyHandler({"http" : 'http://%s' % proxy, "https" : 'https://%s' % proxy})
            self.opener.add_handler(l_proxy_support)
        self.cookies = urllib2.HTTPCookieProcessor(cookiejar)
        self.opener.add_handler(self.cookies)
        self.opener.add_handler(HTTPRefreshProcessor(1000))
        self.default_cookies = None
        

    def get_cookies(self, key):
        cookies = self.cookies.cookiejar._cookies
        for domain in cookies.keys():
            cookies_by_path = cookies[domain]
            for path in cookies_by_path.keys():
                cookies_by_name = cookies_by_path[path]
                if key in cookies_by_name.keys():
                    return cookies_by_name[key]

        return None

    def clear_cookies(self):
        self.cookies.cookiejar._cookies.clear()

    def set_cookie_obj(self, cookie):
        self.cookies.cookiejar.set_cookie(cookie)

    def set_cookie(self, name, value, standard={}):

        cookie = self.cookies.cookiejar._cookie_from_cookie_tuple((name.strip(), value.strip(), standard, {}), self.req)
        self.set_cookie_obj(cookie)

    ##standard had the key [domain, path, port, expires....]
    def set_cookies(self, cookies, standard={}):
        for one in cookies.split(';'):
            self.set_cookie(*one.split('=', 1), **{'standard' : standard})

    def cookies_to_dict(self):
        cookies = self.cookies.cookiejar._cookies_for_request(self.req)
        return dict([(t.name,t.value) for t in cookies])

    def cookies_to_str(self):
        cookies = self.cookies.cookiejar._cookies_for_request(self.req)
        return ';'.join(['%s=%s' % (t.name, t.value) for t in cookies])

    def get_headers(self, headers, req=None):
        for k,v in HEADERS.items():
            if k not in headers:
                headers[k] = v

        if 'referer' not in headers:
            headers['referer'] = self.url
        if req:
            for k, v in headers.items():
                req.add_header(k, v)
            return req
        else:
            return headers


    def make_req(self, url_or_request, data=None, headers={}, muti=False):
        if not isinstance(url_or_request, urllib2.Request):
            headers = self.get_headers(headers)
            self.resp = None
            self.req = urllib2.Request(url_or_request, headers=headers)
            if type(data) == dict:
                if muti:
                    mutipart = MultipartPostHandler()
                    mutipart.http_request(self.req, data)
                else:
                    data = urllib.urlencode(data)
                    self.req.add_data(data)
            else:
                if muti:
                    contenttype = 'multipart/form-data; boundary=---------------------------7d917724f0588'
                    self.req.add_unredirected_header('Content-Type', contenttype)
                else:
                    self.req.add_data(data)
        else:
           self.req = url_or_request
        return self.req

    def get_res(self, *args, **kwargs):
        error = False
        self.exception = None
        self.make_req(*args, **kwargs)
        if self.default_cookies:
            #self.set_cookies(self.default_cookies)
            self.req.add_header('Cookie', self.default_cookies)
            #self.defaultcookies = None
        try:
            resp = self.opener.open(self.req)
            self.resp = resp
            self.retry = 0
            return self.resp
        except Exception, info:
            if self.debug:
                log.exception('')
                if hasattr(info, 'fp'):
                    log.error(info.fp.read())
            self.exception = info
            return None

    def get_form(self, forms, name=None):
        form = None
        if name is None:
            return forms[0]
        else:
            try:
                return forms[name]
            except:
                for item in forms:
                    if item.name == name or item.attrs.get('id', '') == name:
                        return item
        return None


    def submit(self, page, data={}, headers={}, name=None, action=None, kwargs={}):
        forms = ParseFile(StringIO(page), self.resp.geturl(), backwards_compat=False)

        form = self.get_form(forms, name)
        if form == None:
            return None
        for k, v in data.items():
            try:
                item = form.find_control(k)
            except ControlNotFoundError:
                form.new_control('text', k, {'value' : v})
                continue

            if isinstance(item, ListControl) and not isinstance(v, (list, tuple)):
                    v = [v]

            try:
                item.value = v
            except AttributeError:
                if item.readonly:
                    item.readonly = False
                if item.disabled:
                    item.disabled = False
                item.value = v
            except ClientForm.ItemNotFoundError:
                form.controls.remove(item)
                form.new_control('text', item.name, {})
                item = form.find_control(k)
                item.value = v[0]

        if action:
            if callable(action):
                form.action = action(form.action)
            else:
                form.action = action

        req = form.click(**kwargs)
        self.get_headers(headers, req)

        return self.get_page(req)



    def submit_url(self, url, data={}, headers={}, name=None, **kwargs):
        page = self.get_page(url)
        if page is None:
            log.debug("get url %s res None", url)
            return None
        return self.submit(page, data, headers, name, **kwargs)

    def get_page(self, *args, **kwargs):
        if self.get_res(*args, **kwargs) is None:
            return
        try:
            pageData = self.resp.read()
            if self.resp.headers.get('content-encoding', None) == 'gzip':
                pageData = gzip.GzipFile(fileobj=StringIO(pageData)).read()

            self.resp.close()
            return pageData
        except Exception, info:
            if self.debug:
                log.exception('')
            self.exception = info
            return None



    def upload(self, *args, **kwargs):
        kwargs.update({
            'muti' : True
        })
        return self.GetPage(*args, **kwargs)

    @property
    def url(self):
        try:
            return self.resp.url
        except Exception, info:
            #print info
            return ''


if __name__ == '__main__':
    web = SingleWeb(debug=1)
    cookies = 'v=0; tg=5; _cc_=VT5L2FSpdA%3D%3D; _l_g_=Ug%3D%3D; tracknick=crpyrpzcr32; sg=276; lastgetwwmsg=MTM1NDM3NzgzNQ%3D%3D; _tb_token_=MfqCYrBbgl; cookie1=Wqb0SUNieBuVy8Vp7nem%2BMZ2jueAqi0zKzN5P9jTBLQ%3D; cookie2=69294c1a72863eda6d9829cc56a07df6; mt=ci=0_1; cookie17=UoH2iytsQmtB3w%3D%3D; t=a8639831b56e924fe2da2fcdf8774ec5; unb=1092922747; _nk_=crpyrpzcr32; ajs=1; cna=LxhBCTUdkBgCAbcDDhFeemfP; l=crpyrpzcr32::1354381438199::11; swfstore=58016; x=e%3D1%26p%3D*%26s%3D0%26c%3D0%26f%3D0%26g%3D0%26t%3D0; uc1=lltime=1354376660&cookie14=UoLZWGpoi6PCSg%3D%3D&existShop=false&cookie16=WqG3DMC9UpAPBHGz5QBErFxlCA%3D%3D&cookie21=Vq8l%2BKCLiw%3D%3D&tag=7&cookie15=UtASsssmOIJ0bQ%3D%3D; mpp=t%3D1%26m%3D%26h%3D1354378231734%26l%3D1354378233079'
    #web.set_cookies(cookies, {'domain' : '.taobao.com', 'path' : '/'})
    web.default_cookies = cookies
    web.get_page('http://ecrm.taobao.com/mallcoupon/got_bonus.htm')
    for i in range(1):
        web.get_page('http://ecrm.taobao.com/shopbonusapply/buyer_apply.htm?activity_id=28326608&seller_id=38423')
    print web.url
    #web.submit(result)
