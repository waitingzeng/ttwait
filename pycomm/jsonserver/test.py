#! /usr/bin/env python
#coding=utf-8
from gevent.server import StreamServer
from conf.urlconf import patterns
from jsonapp import JsonApp
from gevent.pool import Pool

urlpatterns = patterns('test_views',
    (r'^/index/$', 'index'),
)

PORT = 8888

def main():
    
    # 实例化Application
    app = JsonApp(urlpatterns)
    # 启动StreamServer，pool设置并发连接数
    server = StreamServer(('0.0.0.0', PORT), app, spawn=Pool(1000))
    print '[JSON_APP]Starting GSZ server on port %d'%PORT
    server.serve_forever()


if __name__ == "__main__":
    main()
