#! /usr/bin/env python
#coding=utf-8
"""
For framework author, 
this is a django-like url matching module, you can configure a url setting in
a django way and use this module to resolve a url path to a import string or
a callable or anything you want to match.

This module was extracted from django code, and does not support advanced 
features provided as its origin.

You could contact me if you have any problem: Wei Wu <canri62 AT gmail DOT com>

Example:

       urlpatterns = patterns('',
        (r'^blog/(\d{4})/$', 'blog.views.archive'),
        (r'^user/(?P<name>.*)', 'user.views.index'),
       )
       # create a resolver
       resolver = URLResolver(urlpatterns)
       callback, args, kwargs = resolver.match(PATH_INFO)
  
"""
_resolver_cache = {} # Maps URLconf modules to RegexURLResolver instances.
_callable_cache = {} # Maps view and url pattern names to their view functions.

import re
from utils.functional import memoize
from utils.importlib import import_module

class URLPattern(object):
    def __init__(self, regex, callback, default_args=None, name=None):
        self.regex = re.compile(regex, re.UNICODE)
        self.callback = callback
        self.default_args = default_args or {}
        self.name = name

    def resolve(self, path):
        match = self.regex.search(path)
        if match:
            kwargs = match.groupdict()
            if kwargs:
                args = ()
            else:
                args = match.groups()
            kwargs.update(self.default_args)
            return self.callback, args, kwargs
        return None, None, None
        

            
class URLResolver(object):
    def __init__(self, regex, urlpatterns):
        self._regex = regex
        self.regex = re.compile(regex, re.UNICODE)
        self.urlpatterns = urlpatterns

    def resolve(self, path):
        tried = []
        match = self.regex.search(path)
        if match:
            new_path = path[match.end():]
            for pattern in self.urlpatterns:
                res = pattern.resolve(new_path)
                if res:
                    return res

        
def patterns(prefix, *args):
    pattern_list = []
    for t in args:
        if isinstance(t, (list, tuple)):
            t = url(prefix=prefix, *t)
        elif isinstance(t, URLPattern):
            # TODO check here
            t.add_prefix(prefix)
        pattern_list.append(t)
    return tuple(pattern_list)

def url(regex, view, kwargs=None, name=None, prefix=''):
    if type(view) == tuple:
        return URLResolver(regex, view)
    else:
        if isinstance(view, basestring):
            if not view:
                # TODO
                raise 'HTTP 404 Not Found'
            if prefix:
                view = prefix + '.' + view
        return URLPattern(regex, view, kwargs, name)

def get_resolver(urlconf):
    return URLResolver(r'^/', urlconf)
get_resolver = memoize(get_resolver, _resolver_cache, 1)



def get_mod_func(callback):
    # Converts 'django.views.news.stories.story_detail' to
    # ['django.views.news.stories', 'story_detail']
    try:
        dot = callback.rindex('.')
    except ValueError:
        return callback, ''
    return callback[:dot], callback[dot+1:]


def get_callable(lookup_view, can_fail=False):
    if not callable(lookup_view):
        try:
            # Bail early for non-ASCII strings (they can't be functions).
            lookup_view = lookup_view.encode('ascii')
            mod_name, func_name = get_mod_func(lookup_view)
            if func_name != '':
                lookup_view = getattr(import_module(mod_name), func_name)
                if not callable(lookup_view):
                    raise AttributeError("'%s.%s' is not a callable." % (mod_name, func_name))
        except (ImportError, AttributeError):
            if not can_fail:
                raise
        except UnicodeEncodeError:
            pass
    return lookup_view
get_callable = memoize(get_callable, _callable_cache, 1)



if __name__ == '__main__':
    def hello(aaa):
        print aaa
    
    urlpatterns1 = patterns('',
        (r'^blog/(\d{4})/$', 'views.archive'),
        (r'^hello/(\d{4})/$', hello),
        
    )
    
    urlpatterns = patterns('blog',
        (r'^blog/(\d{4})/$', 'views.archive'),
        (r'^hello/', urlpatterns1),
        (r'^user/(?P<name>.*)', 'user.views.index'),
    )
    mapper = get_resolver(urlpatterns)
    #print mapper.resolve('/blog/2009/')
    print mapper.resolve('/hello/hello/2009/')
    print mapper.resolve('/user/hupo')
    #print mapper.resolve('not/exist')
