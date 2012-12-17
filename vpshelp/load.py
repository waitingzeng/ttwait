#! /usr/bin/env python
#coding=utf-8
import os
import os.path as osp
import sys
from optparse import OptionParser
import urlparse
import urllib2

curdir = osp.abspath('.')
parser = OptionParser()
parser.add_option("-n", "--name", dest="name",
                  help="the name want to download", action='store', type='string')
parser.add_option("-t", "--type", dest="type",
                  help="the type want to download", action='store', type='string')
parser.add_option("-a", "--target", dest="target",
                  help="the target want to append", action='store', type='string')

parser.add_option("-b", "--begin", dest='begin', help="the begin", action='store', type='int', default=0)
parser.add_option("-e", "--end", dest='end', help="the end", action='store', type='int', default=0)

baseurl = 'http://ttwait-ttwait.stor.sinaapp.com/'

def get_fail_data():
    url = 'http://pic.caatashoes.com/account/fails.zip'
    os.chdir('/root/data')
    if not osp.exists('fails.txt'):
        if not os.path.exists('fails.zip'):
            a = urllib2.urlopen(url).read()
            file('fails.zip', 'wb').write(a)
        os.popen('unzip -n fails.zip').read()
    d = {}
    for line in file('fails.txt'):
        d[line.strip()] = 1
    os.chdir(curdir)
    return d

fails = get_fail_data()
print 'get fail data', len(fails)
def download(name):
    basename = osp.basename(name)
    base, ext = osp.splitext(basename)
    if not osp.exists(basename):
        url = urlparse.urljoin(baseurl, name)
        url = "wget %s -t 2" % url
        for i in range(3):
            if not osp.exists(basename):
                print os.popen(url).read()
            else:
                break
    if ext == '.zip' and not osp.exists('%s.txt' % base):
        print os.popen('unzip -n %s' % basename).read()
     
    
    
def load():
    options, args = parser.parse_args(sys.argv[1:])
    if options.end < options.begin:
        print 'end must gt begin'
        parser.print_help()
        return
    
    if not options.target:
        options.target = 'all.txt'
    
    if options.type == 'send':
        os.popen('rm -rf %s' % options.target)
        options.name = 'http://pic.caatashoes.com/account/cache_sender_%s.zip'
            
    if options.type == 'friend':
        options.target = ''
        options.name = 'http://pic.caatashoes.com/friends/tos_%s.zip'
        
    for i in range(options.begin, options.end):
        name = options.name % i
        download(name)
        if options.type == 'send':
            out = file(options.target, 'a')
            for line in file('cache_sender_%s.txt' % i):
                if line.strip() in fails:
                    continue
                out.write(line)
            out.close()

if __name__ == '__main__':
    load()