#!/usr/bin/python
#coding=utf8
import sys
import os.path as osp
import urlparse
from tornado.web import RequestHandler, HTTPError
from pycomm.utils.pprint import pformat
from pycomm.log import PrefixLog
from pycomm.utils.user_agent import UserAgent
from pycomm.utils.storage import Storage
from urls_helper import urls_helper
import ujson as json


class UrlHandlerType(type):
    def __new__(cls, name, bases, dct):
        res = type.__new__(cls, name, bases, dct)
        if name.lower() not in ('RequestHandler', 'BaseHandler') and not name.startswith('_'):
            urls_helper.add_handler(res)
        return res
    

class BaseHandler(RequestHandler):
    __metaclass__ = UrlHandlerType
    detect_user_agent = False
    default_template_path = 'web'
    controller_path = 'controller'

    on_finish_callback = {}
    
    @classmethod
    def register_finish_callback(cls, func, pri=0):
        if isinstance(cls.on_finish_callback, list):
            raise Exception("run time can not register finish callback")
        cls.on_finish_callback[func] = pri

    @classmethod
    def run_finish_callback(cls, handler):
        if isinstance(cls.on_finish_callback, dict):
            self.on_finish_callback = sorted(on_finish_callback.iteritems(), key=operator.itemgetter(1), reverse=True)

        for func in self.on_finish_callback:
            func(handler)


    def __init__(self, *args, **kwargs):
        RequestHandler.__init__(self, *args, **kwargs)
        self.log = PrefixLog('%s[%s]' % (self.request.method, self.request.path))
        self.init()
        
    def on_finish(self):

        self.log.trace("finish handler")

    def init(self):

        self._settings = Storage(self.application.settings)

        self.user_agent = UserAgent(self.request.headers["User-Agent"])
        #self.user_agent.agent_lower, self.user_agent.is_mobile
        self.device = self.get_device() if self.detect_user_agent else self.default_template_path

        self.log.trace("begin handler")

    @property
    def settings(self):
        return self._settings

    def clear_tpl_cache(self):
        with RequestHandler._template_loader_lock:
            for loader in RequestHandler._template_loaders.values():
                loader.reset()
        
    def render_string(self, template_name, **kwargs):
        if self.detect_user_agent:
            template_name = osp.join(self.device, template_name)
        else:
            template_name = osp.join(self.default_template_path, template_name)

        return RequestHandler.render_string(self, template_name, **kwargs)
        
    def render_json_string(self, **kwargs):
        content_type = kwargs.pop('content_type', 'application/json')
        self.set_header('Content-Type', content_type)
        data = json.dumps(kwargs)
        self.log.trace("%s", data)
        return data

    def render_json(self, **kwargs):
        self.write(self.render_json_string(**kwargs))
        self.finish()

    def set_cache(self, seconds, is_privacy=None):
        if seconds <= 0:
            self.set_header('Cache-Control', 'no-cache')
            #self.set_header('Expires', 'Fri, 01 Jan 1990 00:00:00 GMT')
        else:
            if is_privacy:
                privacy = 'public, '
            elif is_privacy is None:
                privacy = ''
            else:
                privacy = 'private, '
            self.set_header('Cache-Control', '%smax-age=%s' % (privacy, seconds))
    

    def get_template_namespace(self, **kwargs):
        context = RequestHandler.get_template_namespace(self)
        context.update(self.get_ext_info())
        context['settings'] = self.settings
        context['device'] = self.device
        context['js_url'] = self.js_url
        context['css_url'] = self.css_url
        context['pformat'] = pformat
        context['debug'] = self.settings.get('debug', False)
        context.update(kwargs)
        return context

    def get_ext_info(self):
        return {}

    def get_int(self, name, default=0):
        try:
            return int(self.get_argument(name))
        except:
            return default

    def get_device(self):
        if self.user_agent.is_mobile:
            return self.settings.mobile_theme
        return self.settings.theme


    def js_url(self, filename, prefix=False):
        filename = filename.strip()
        if prefix:
            return urlparse.urljoin(self.settings.js_resource_url, filename)
        return self.static_url( osp.join('js', self.device, filename))

    def css_url(self, filename, prefix=False):
        filename = filename.strip()
        if prefix:
            return urlparse.urljoin(self.settings.css_resource_url, filename)
        return self.static_url(osp.join('css', self.device, filename))

    def clear_cookie(self, name, path="/", domain=None):
        if domain is None:
            domain = self.settings.get('cookie_domain', '')
        return RequestHandler.clear_cookie(self, name, path, domain)


    def _handle_request_exception(self, e):
        if not isinstance(e, HTTPError):
            self.log.error("%s", self.request)
            self.log.exception(exc_info=True)

            return self.send_error(500, exc_info=sys.exc_info())
        return RequestHandler._handle_request_exception(self, e)

    def get_forms(self):
        pass
    
