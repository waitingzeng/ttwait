#! /usr/bin/env python
#coding=utf-8
import os
import os.path as osp
import time
import gettext as gettext_module
from copy import deepcopy
from py3rd import webpy
from py3rd.webpy.webapi import rawinput

from pycomm.core.hostconfig import deep_merge
from pycomm.log import oss
from pycomm.tools.track_time import TrackTime
from pycomm.log.oss import MonitorHelper
from pycomm.log import log
from pycomm.weblib.safeinput import SafeInput
from pycomm.shortcuts import get_conf, get_template, get_i18n_dir
from pycomm.utils.html import add_querystr
from pycomm import template
from pycomm.utils.datastructures import Storage
from filetypes import HttpHeader


class EmptySession(dict):
    def kill(self):
        pass


def remote_ip():
    remote_ip = webpy.ctx.env.get('PROXY_FORWARDED_FOR', '')
    if not remote_ip:
        remote_ip = webpy.ctx.env.get('REMOTE_ADDR')

    if remote_ip.find('.') == -1:
        ips = []
        for i in range(0, len(remote_ip), 2):
            ips.append('%s' % int(remote_ip[i:i+2], 16))
        ips = ips[::-1]
        remote_ip = '.'.join(ips)

    return remote_ip
client_ip = remote_ip


def referer():
    return webpy.ctx.env.get('HTTP_REFERER', '')


class TemplateLoader(template.Loader):
    def __init__(self, default_lang='zh_CN'):
        self.default_lang = default_lang
        super(TemplateLoader, self).__init__(osp.abspath(get_template('')))

    def get_tpl_name(self, lang, appname, name):
        p1 = osp.join(lang, appname, name)
        if osp.exists(osp.join(self.root, p1)):
            return p1
        p2 = osp.join(lang, name)
        if osp.exists(osp.join(self.root, p2)):
            return p2
        p3 = osp.join(appname, name)
        if osp.exists(osp.join(self.root, p3)):
            return p3
        if osp.exists(osp.join(self.root, name)):
            return name
        
        raise Exception('Template Does Not Exists %s/%s/%s/%s' % (self.root, lang, appname, name))

    def resolve_path(self, name, parent_path=None):
        fullname = super(TemplateLoader, self).resolve_path(name, parent_path)
        if osp.exists(osp.join(self.root, fullname)):
            return fullname
        basename = osp.basename(fullname)
        dirname = osp.dirname(fullname)
        while dirname:
            dirname = osp.dirname(dirname)
            name = osp.join(dirname, basename)
            if osp.exists(osp.join(self.root, name)):
                return name
        raise Exception('Template Does Not Exists %s' % fullname)

    def load(self, name, parent_path=None, lang='', appname=''):
        """Loads a template."""
        if parent_path:
            name = self.resolve_path(name, parent_path=parent_path)
        else:
            name = self.get_tpl_name(lang, appname, name)
        key = osp.join(lang, appname, name)
        if webpy.config.debug or name not in self.templates:
            tpl_name = self.get_tpl_name(lang, appname, name)
            self.templates[key] = self._create_template(name)
        return self.templates[key]



loader = TemplateLoader()

class BaseRequest(object):
    APPNAME = ''
    DEFAULT_LANG = 'zh_CN'
    ALLOW_LANG = ('zh_CN', 'en_US')
    CONTENT_TYPE = 'text/html'
    SETTINGS = None
    SETTINGS_CACHE = {}
    RES_CACHE = None
    I18N_CACHE = False

    def __init__(self):
        if not self.SETTINGS:
            log.trace('Not Set BaseRequest SETTINGS')
            self.SETTINGS = {}
        self.uri = webpy.ctx['path']
        self.GET = self._wrap(self.GET)
        self.POST = self._wrap(self.POST)

        self._init()
        self.lang = self.get_lang()
        self.load_i18n()
        self.init()
    
    def _init(self):
        self.cookies = SafeInput(webpy.cookies())
        self.input = SafeInput(rawinput())
        self.method = webpy.ctx.method.lower()
        
        webpy.header('Content-Type', '%s;charset=utf-8' % self.CONTENT_TYPE)
        webpy.header('Cache-Control', 'no-cache, must-revalidate')
    
    def init(self):
        pass

    @property
    def remote_ip(self):
        return remote_ip()
    
    @property
    def referer(self):
        return referer()

    def GET(self):
        raise NotImplementedError

    def POST(self):
        raise NotImplementedError

    def _wrap(self, func):
        def __wrap(*args, **kwargs):
            t = TrackTime(self.__class__.__name__)
            cls_mon = MonitorHelper(self.__class__.__name__, 0, webpy.ctx['method'])
            res = func(*args, **kwargs)
            cls_mon.close()

            diff = t.get_time()
            if diff > 1000:
                log.trace("URI %s run long time %d", self.uri, diff)

            t.stop()
            return res
        __wrap.__name__ = func.__name__
        return __wrap
    
    def get_domain_lang(self):
        homedomain = webpy.ctx.host.split(':', 1)[0]

        if self.SETTINGS.setdefault('domain_langs', {}):
            for domain, target_lang in self.SETTINGS.domain_langs.items():
                if homedomain.endswith(domain):
                    return target_lang
        return None

    def get_lang(self):
        lang = self.input.get('lang', None)
        
        self.SETTINGS.setdefault('allow_langs', [self.DEFAULT_LANG])
        if lang and isinstance(lang, (tuple, list)):
            lang = lang[-1]
        if not lang or lang not in self.SETTINGS.allow_langs:
            lang = self.get_domain_lang()
            if not lang or lang not in self.SETTINGS.allow_langs:
                return self.SETTINGS.setdefault('default_lang', self.DEFAULT_LANG)
        
        
        return lang

    def extra_init(self):
        return {}

    def _initializer(self):
        obj = {
            'lang' : self.lang,
            'static' : '/static',
            'langstatic' : '/static/%s' % self.lang,
            'jslib' : '/static/lib/js',
            'csslib' : '/static/lib/css',
            'imglib' : '/static/lib/images',
            'jspath' : '/static/%s/%s/js' % (self.lang, self.APPNAME),
            'imgpath' : '/static/%s/%s/images' % (self.lang, self.APPNAME),
            'csspath' : '/static/%s/%s/css' % (self.lang, self.APPNAME),
            'ctx' : webpy.ctx,
            'settings' : self.settings,
            '_' : self.gettext,
            'get_res' : self.get_res,
            't' : int(time.time()),
        }
        obj.update(self.extra_init())
        return obj
    
    def load_i18n(self):
        if self.settings.setdefault('use_i18n', False):
            if not self.__class__.I18N_CACHE:
                gettext_module.install('messages', get_i18n_dir(), unicode=True)
                self.__class__.I18N_CACHE = True
            try:
                self._gettext = gettext_module.translation('messages', get_i18n_dir(), languages=[self.lang])
            except IOError:
                self._gettext = gettext_module.NullTranslations()
        
     

    def gettext(self, message):
        if not self.settings.use_i18n:
            return message
        return self._gettext.ugettext(message)
    _ = gettext

    def render(self, name, **kwargs):
        '''
        传入模板的参数有：1.基类传入的字典变量，2._initializer字典变量 3.子类实现的extra_init字典变量
        '''
        tpl = loader.load(name, lang=self.lang, appname=self.APPNAME)
        context = self._initializer()
        context.update(kwargs)
        return tpl.generate(**context)

    @property
    def settings(self):
        d = self.SETTINGS_CACHE.get(self.lang, {})
        if not d:
            if not self.SETTINGS:
                return d
            if self.lang in self.SETTINGS:
                d = deepcopy(self.SETTINGS)
                deep_merge(d, d[self.lang])
                del d[self.lang]
                d = Storage(d)
            else:
                d = self.SETTINGS
            self.SETTINGS_CACHE[self.lang] = d

        return d

    def get_res(self, *args):
        res_path = osp.join(*args)
        if BaseRequest.RES_CACHE is None:
            BaseRequest.RES_CACHE = {}
            res = get_conf('res.conf')
            if osp.exists(res):
                for line in file(res):
                    line = line.strip()
                    if not line:
                        continue
                    path, mtime = line.split('\t')
                    BaseRequest.RES_CACHE[path] = mtime
        return add_querystr(res_path, 'v=%s' % BaseRequest.RES_CACHE.get(res_path, ''))

    @classmethod
    def direct_to_tpl(cls, tpl_name, **kwargs):
        def _wrap():
            ins = cls()
            return ins.render(tpl_name, **kwargs)
        return _wrap

    @classmethod
    def direct_to_file(cls, base_path, **kwargs):
        if not osp.exists(base_path):
            raise Exception('%s does not exists' % base_path)
        buf_size = 1024
        class DirectFileClass(object):
            def get_index(self, path):
                if osp.isdir(path):
                    for name in ['index.html', 'default.html']:
                        newpath = osp.join(path, name)
                        if osp.exists(newpath):
                            return newpath
                    return None
                return path


            def GET(self, path):
                path = osp.join(base_path, path)
                if not osp.exists(path):
                    raise webpy.NotFound()
                path = self.get_index(path)
                if not path:
                    raise webpy.NotFound()
                     
                name, ext = osp.splitext(path)
                content_type = HttpHeader.data.get(ext[1:], HttpHeader.default)
                webpy.header('content-type', content_type)
                if not (content_type.startswith('text') or content_type.startswith('image')):
                    webpy.header('Content-disposition', 'attachment; filename=%s' % osp.basename(path))
                
                
                
                f = file(path, 'rb')
                try:
                    
                    while True:  
                        c = f.read(buf_size)  
                        if c:  
                            yield c  
                        else:  
                            break 
                except:
                    log.exception('read %s fail' % path)
                    yield ''
                finally:
                    f.close()
        return DirectFileClass
