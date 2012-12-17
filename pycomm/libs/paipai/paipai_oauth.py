#!/usr/bin/python2.7
#coding=utf8
import random
import time
import ujson as json
import hashlib
import base64
import hmac
import urllib
from pycomm.log import log
from pycomm.utils.storage import Const
from pycomm.singleweb import SingleWeb
from mfhui_admin.comm_def import PaiPaiRequestDealState as RequestDealState
from mfhui_admin.comm_def import PaiPaiResponseDealState as ResponseDealState
from mfhui_admin.comm_def import PaiPaiDealType as DealType


class PaiPaiOpenApiOauth(object):
    CHARSET = 'utf-8'
    FORMAT = 'json'
    HOSTNAME = 'http://api.paipai.com'
    #HOSTNAME = 'http://apitest.paipai.com'
    METHOD = 'get'

    def __init__(self, app_oauthid, app_oauth_key, access_token, uin, **kwargs):
        self.uin = uin
        self.app_oauth_key = app_oauth_key
        self.access_token = access_token
        self.app_authid = app_oauthid
        self.params = {}
        self.debugon = False
        self.web = SingleWeb()

    def get_default_params(self):
        params = {}
        params['randomValue'] = random.random() * 100000 + 11229
        params['timeStamp'] = int(time.time())
        params['appOAuthID'] = self.app_authid
        params['accessToken'] = self.access_token
        params['pureData'] = '1'
        params['uin'] = self.uin
        params['sellerUin'] = self.uin
        params['format'] = self.FORMAT
        params['charset'] = self.CHARSET
        return params


    def invoke_open_api(self, api_path, kwargs):
        params = self.get_default_params()
        params.update(kwargs)
        
        # 第二步： 构造密钥。得到密钥的方式：在应用的appOAuthkey末尾加上一个字节的“&”，即appOAuthkey&
        secret = self.app_oauth_key + "&"

        #生成签名，使用HMAC-SHA1加密算法，将Step1中的到的源串以及Step2中得到的密钥进行加密。然后将加密后的字符串经过Base64编码。
        sign = self.make_sign(api_path, params)
        params["sign"] = sign

        #echo "@@@@:invokeOpenApi: sign :" ;var_dump( $sign);echo "<br/>";
        #echo "@@@@:invokeOpenApi: encodeUrl(sign) :" ;var_dump($this->encodeUrl($sign));echo "<br/>";
        url = '%s%s?' % (self.HOSTNAME, api_path) 

        if self.METHOD == 'get':
            url += urllib.urlencode(params)
            res = self.web.get_page(url)
        else:
            res = self.web.get_page(url, params)
        return res


    def invoke(self, api_path, params):
        log.trace('invoke %s params %s', api_path, params)
        res = self.invoke_open_api(api_path, params)
        if not res:
            return None
        res = res.strip()
        try:
            res = json.loads(res)
            if res['errorCode'] != 0:
                log.error('call %s fail %s', self.uin, res['errorMessage'])
            return res

        except:
            log.debug(res)


    
    def make_sign(self, api_path, params):
        """
        /**
         * 第三步：生成签名值。
         * 1. 使用HMAC-SHA1加密算法，将Step1中的到的源串以及Step2中得到的密钥进行加密。
         * 2. 然后将加密后的字符串经过Base64编码。
         * 3. 得到的签名值结果如下：
         *
         * more,to see: http://php.net/manual/en/function.hash-hmac.php
         * @param $method
         * @param $secret
         */
         """
        #echo "@@@@:makeSign: (secret)  :" ;var_dump($secret);echo "<br/>";
        #获取需要加密的原串
        mk = self.make_source(self.METHOD, api_path, params)
        #echo "@@@@:makeSign: makeSign(mk) Src String :" ;var_dump($mk);echo "<br/>";
        #使用sha1 加密算法加密
        #注意：这里必须设置为true： When set to TRUE, outputs raw binary data. FALSE outputs lowercase hexits.
        hash = hmac.new(self.app_oauth_key + '&', mk, hashlib.sha1)

        #将加密后的字符串用base64方式编码
        sig = base64.b64encode(hash.digest())
        return sig


    
    def make_source(self, method, urlpath, params):
        """
        /**
         * 构造原串
         * 源串是由3部分内容用“&”拼接起来的：   HTTP请求方式 & urlencode(uri) & urlencode(a=x&b=y&...)
         * @param $method  get | post
         * @param $urlPath if our url is http://api.paipai.com/deal/sellerSearchDealList.xhtml,then
         * $urlPath=/deal/sellerSearchDealList.xhtml
         */
        """
        keys = params.keys()
        keys.sort()
        #先拼装  HTTP请求方式 & urlencode(uri) &
        buffer = []
        buffer.append(method.upper())
        buffer.append(urllib.quote_plus(urlpath))
        #拼装 参数部分
        buffer2 = []
        for k in keys:
            buffer2.append('%s=%s' % (k, params[k]))
        #组装成预期的“原串”
        print '&'.join(buffer2)
        buffer.append(urllib.quote_plus(str('&'.join(buffer2))))

        return '&'.join(buffer)


def test():
    app = PaiPaiOpenApiOauth('700068542', 'aRvr6i7p70Bai2XF', '6b8d60607dbe7158d1dcae72d242a0c8', '171322809')
    data = {
        'sellerUin' : '171322809',
        'dealState' : RequestDealState.DS_WAIT_SELLER_DELIVERY,
        'dealType' : DealType.ALL,
        'listItem' : '1',
    }
    print app.invoke('/deal/sellerSearchDealList.xhtml', data)


if __name__ == '__main__':
    test()
