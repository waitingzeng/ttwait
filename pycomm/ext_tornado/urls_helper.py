#!/usr/bin/python
#coding=utf8
import os.path as osp
import inspect
from pprint import pprint
from pycomm.log import log


class UrlsHelper(object):
    def __init__(self):
        self.handlers = []

    def add_handler(self, handler):
        if handler not in self.handlers:
            self.handlers.append(handler)


    def get_url_name(self, name):
        n = []
        for x in name:
            if x >= 'A' and x <= 'Z':
                n.append('_')
            n.append(x)
        n = ''.join(n)
        return n.strip('_').lower()

    def get_base_urls(self, handler, controller_path):
        abspath = osp.abspath(inspect.getsourcefile(handler)).lower()
        abspath = abspath.replace('\\', '/')

        if abspath.find(controller_path) == -1:
            raise StopIteration

        base_url = abspath.split(controller_path)[-1]
        base_url = base_url.rsplit('.', 1)[0]

        url_name = self.get_url_name(handler.__name__)
        
        yield base_url + '/' + url_name

        if url_name == 'index':
            yield base_url
        
        

    def get_handler_urls(self, handler, controller_path):
        
        urls = getattr(handler, 'urls', [])
        if urls:
            for url in urls:
                yield (url, handler)
            return
        

        
        get_urls = self.get_func_urls(handler.get)
        post_urls = self.get_func_urls(handler.post)

        if get_urls is None and post_urls is None:
            raise StopIteration

        log.debug('handler %s get_urls %s  post_urls %s',  handler.__name__, get_urls, post_urls)
        sub_urls = get_urls or []
        for url in post_urls or []:
            if url not in sub_urls:
                sub_urls.append(url)


        for base_url in self.get_base_urls(handler, controller_path):
            if not sub_urls:
                yield (base_url, handler)
                if not base_url.endswith('/'):
                    yield (base_url + '/', handler)    
            for x in sub_urls:
                yield (base_url + '/' + x, handler)
                if x:
                    yield (base_url + '/' + x + '/', handler)
                else:
                    yield (base_url, handler)

    def get_args_re(self, name):
        if name.endswith('id') or name.find('page') != -1 or name in ['limit']:
            return '(\d+)'
        return '(.+)'


    def get_func_urls(self, get_func):
        arg = inspect.getargspec(get_func)
        args = arg.args
        print get_func, args
        if len(args) == 1:
            return []
        args.remove('self')
        urls = []
        args_re = [self.get_args_re(x) for x in args]

        urls.append('/'.join(args_re))

        defaults_len = arg.defaults and len(arg.defaults) or 0

        if defaults_len:
            for i in range(defaults_len):
                args_re.pop()
                if args_re:
                    urls.append('/'.join(args_re))
                else:
                    urls.append('')

        return urls


    def sort_urls(self, all_urls):
        url_no_re = []
        url_num_re = []
        url_all_re = []
        for handler in all_urls:
            url = handler[0]
            if url.endswith('(.+)') or url.endswith('(.+)/'):
                url_all_re.append(handler)
            elif url.endswith('(\d+)') or url.endswith('(\d+)/'):
                url_num_re.append(handler)
            else:
                url_no_re.append(handler)

        url_all_re.sort()
        url_num_re.sort()
        url_no_re.sort()
        return url_no_re + url_num_re + url_all_re

    def get_urls(self, controller_path):
        all_urls = []
        for handler in self.handlers:
            name = handler.__name__.lower()
            if name.startswith('_') or name.startswith('base'):
                continue
            all_urls.extend(self.get_handler_urls(handler, controller_path))

        
        if len(dict(all_urls)) != len(all_urls):
            log.error('had dupl urls')

        #all_urls = self.sort_urls(all_urls)

        return all_urls


urls_helper = UrlsHelper()
