import re
import urllib2
import urllib
from pycomm.log import log

TAGRESULT = re.compile(r'<Result>(.*?)<\/Result>', re.I|re.M|re.S)
def get_yahoo_tags(content):
    try:

        data = {
            'appid' : 'F20C_5fV34GKK0OIuUKOGwrjY253x4Zjt_qyV.vFIq9hPH5h5AADBJNeYO0mDgoyOmVk',
            'context' : content,
        }
        url = 'http://api.search.yahoo.com/ContentAnalysisService/V1/termExtraction'
        req = urllib2.Request(url, urllib.urlencode(data))
        res = urllib2.urlopen(req).read()
        r = TAGRESULT.findall(res)
    except:
        log.exception('')
        return []
    return r
