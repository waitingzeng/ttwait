# coding:utf-8

from pycomm.singleweb import get_page
#from pyquery import PyQuery
from pycomm.log import log
from pycomm.utils import text
import json

# u'QueryResult' -> should be True
def query138(m):
    m = int(m)
    assert m> 1000000 # atleast
    url = "http://www.ip138.com:8080/search.asp?mobile=%s&action=mobile"
    res = get_page(url % m)
    if not res:
        log.error("get url %s fail", url)
        return None

    owner = PyQuery(res).find('table').eq(1).find('tr').eq(2).find('td').eq(1).text()
    if not owner:
        log.error('parse owner fail m %s %s', m, res)
        return None
    return owner.strip("'")


def query(m):
    m = int(m)
    assert m> 1000000 # atleast
    url = "http://api.showji.com/Locating/www.showji.com.aspx?m=%s&output=json&callback=querycallback"
    res = get_page(url % m, headers={'referer' : 'http://guishu.showji.com/search.htm?m=%s' % m})
    if not res:
        log.error("get url %s fail", url)
        return None

    data = text.get_in(res, 'querycallback(', ')')
    if res:
        try:
            data = json.loads(data)
            if data['QueryResult'] == 'True' and data['Province']:
                return data
        except:
            pass
    log.error('parse owner fail m %s %s', m, res)
    return None
            

if __name__== '__main__':
     print query(15920484032)
