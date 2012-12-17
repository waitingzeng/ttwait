#! /usr/bin/env python
#coding=utf-8
import sys
import os
import os.path as osp
import random
import urllib2
import traceback

cur_dir = osp.dirname(__file__)

def post_blog(name):
    target_dir = 'D:\\Code\\Python\\SEO\\link'
    sys.path.append(target_dir)
    os.chdir(target_dir)
    lines = file('makemoney/account.txt').read().split('\n')
    f = file('makemoney/account.txt', 'w')
    newline = 'Wordpress|%s|TTwait846266|http://mainsite.sinaapp.com/%s/' % (name, name)
    had = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line == newline:
            had = True
        else:
            if not line.startswith('#'):
                line = '#' + line
        f.write(line)
        f.write('\n')
    
    f.close()
    
    from autoblog import AutoPost
    app = AutoPost('makemoney')
    app.run(random.randint(20, 40))
    sys.path.pop()
    

def create_blog(name):
    target_url = 'http://mainsite.sinaapp.com/wp-admin/network/autocreate.php?domain=%s&noauth=1' % name
    try:
        res = urllib2.urlopen(target_url).read()
        res = res.strip()
        if res == 'success':
            print 'create blog success', name
            return True
        elif res.find('站点已存在') != -1:
            print 'blog exists', name
            return True
        else:
            print target_url
            print res
            return False
    except:
        traceback.print_exc()
        print 'create blog fail', name
    return False

def run():
    name = sys.argv[1]
    if not create_blog(name):
        return
    post_blog(name)



if __name__ == '__main__':
    create_blog('zqc')
    #post_blog(sys.argv[1])
    
        