#! /usr/bin/env python
#coding=utf-8
from site_config import SiteUrl
import urllib2
import re

id_re = re.compile(r'/(\d+)/i\.html', re.I | re.M)

f = file('categorys.txt', 'w')
for k, v in SiteUrl.items():
    url = 'http://%s/allcategories/all-categories' % v
    data = urllib2.urlopen(url).read()
    id_list = id_re.findall(data)
    f.write('\n'.join('%s\t%s' % (k, x) for x in id_list))
    f.write('\n')
    print k, 'finish'
