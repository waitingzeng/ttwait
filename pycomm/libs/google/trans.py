#! /usr/bin/env python
#coding=utf-8
#import sitecustomize
from dict4ini import DictIni
from singleweb import get_page
import json
from text import make_utf8, readdict
import urllib
import urllib2
from random import randint
import traceback
import re

lang_dict = {
    'ar' : '阿拉伯文',
    'bg' :	'保加利亚文',
    'ca' :	'加泰罗尼亚文(西班牙)',
    'cs' :	'捷克语',
    'da' :	'丹麦语',
    'de' :	'德语',
    'el' :	'希腊语',
    'en' :	'英语',
    'es' :	'西班牙语',
    'et' :	'爱沙尼亚语',
    'fi' :	'芬兰语',
    'fr' :	'法语',
    'gl' :	'盖尔文(爱尔兰)',
    'hi' :	'印度文',
    'hr' :	'克罗地亚文',
    'hu' :	'匈牙利语',
    'id' :	'印尼文',
    'it' :	'意大利语',
    'iw' :	'希伯来语',
    'ja' :	'日语',
    'ko' :	'朝鲜语',
    'lt' :	'立陶宛语',
    'lv' :	'拉脱维亚语',
    'mt' :	'马耳他文',
    'nl' :	'荷兰语',
    'no' :	'挪威语',
    'pl' :	'波兰语',
    'pt' :	'葡萄牙语',
    'ro' :	'罗马尼亚语',
    'ru' :	'俄语',
    'sk' :	'斯洛伐克文',
    'sl' :	'斯拉维尼亚文',
    'sq' :	'阿尔巴尼亚文',
    'sr' :	'塞尔维亚文',
    'sv' :	'瑞典语',
    'th' :	'泰文',
    'tl' :	'菲律宾文',
    'tr' :	'土耳其文',
    'uk' :	'乌克兰文',
    'vi' :	'越南文',
    'zh-CN' :   '中文(简体)',
    'zh-TW' :   '中文(繁体)',
}


langs = lang_dict.keys()

dot_re = re.compile('[,]{2:}')
def translate_by_web(content, to_lang='en'):
    data = {
        'client' : 't',
        'text' : content,
        'hl' : 'en',
        'sl' : 'auto',
        'tl' : to_lang,
        'pc' : '0',
        'otf' : '1'
    }
    url = 'http://translate.google.com/translate_a/t'
    res = get_page(url, data)
    if not res:
        print 'trans page is None'
        return None
    file('a1.txt', 'w').write(res)
    res = re.sub(',+', ',', res)
    try:
        res = json.loads(make_utf8(res))
    except:
        traceback.print_exc()
        file('a.txt', 'w').write(res)
        return None
    data = []
    for item in res[0]:
        data.append(item[0])
    return ''.join(data)

def translate_by_ajax(content, to_lang='en'):
    
    if not content.strip():
        return content
    data = {
        'v' : '1.0',
        'q' : content,
        'hl' : 'en',
        'langpair' : '|' + to_lang
    }
    url = 'http://ajax.googleapis.com/ajax/services/language/translate?' + urllib.urlencode(data)
    res = get_page(url)
    if res is None:
        print 'ajax trans page is None'
        return None
    res = json.loads(make_utf8(res))
    if res['responseStatus'] != 200:
        return None
    return res['responseData']['translatedText']

def translate(content, to_lang='en'):
    if len(content) < 1024:
        return translate_by_ajax(content, to_lang)
    else:
        return '\n'.join([translate_by_ajax(x) for x in content.split('\n') if x])

translate = translate_by_web

def rnd_trans(content, to_lang='en', times=3):
    oldcontent = content
    for i in range(times):
        tl = langs[randint(0, len(langs)-1)]
        try:
            content = translate(content, tl)
        except:
            continue
    try:
        return translate(content, to_lang)
    except:
        traceback.print_exc()
        return oldcontent

if __name__ == '__main__':
    #print translate(u'你好')
    translate("""Whether you're new to trading or you are what's considered a "seasoned" trader, there is a lot of money to be made trading """,  to_lang='zh-CN')
        