#!/usr/bin/python
#coding=utf8
from pycomm.singleweb import SingleWeb
from pycomm.log import log


class TaobaoWeb(object):
    pjs = None
    def __init__(self, user_name, password):
        self.user_name = user_name
        self.password = password
        self.web = SingleWeb(debug=1)

    def pjs_login(self):
        pass

    def login(self):

        url = 'https://login.taobao.com/member/login.jhtml'        
        data = {
            'TPL_username' : self.user_name,
            'TPL_password' : self.password,
            'ua' :  '255XUeLg6YFz72JEh01cNMNYT8=|XsQIRVFF2j5Odm1L/3Sy6snh+7WhRTY=|X0SIxdBb9ZmoPzF5jSaI5NNPg4uuBdOLsy/gh4IR17Oeg03lIsY=|WMUJLzvf|WUeLrbld|WkBOKY6FGvKHPqCJbR6xbwcxbMvy90yI6tOe0Dhd5z1bYzm3rt1yrMTyrwiQrWK41fRqhU2ubDACm1axlC/5pZQMQuWSjqlPPAVO4CW4A+PEfmULgw6dWy4CVD/6xwjgkYULAUXO2ZOgBJtLIkmGRDSGnFOHkinz1U8cOo6FGvKHPm6pTfgjzeJZQ4yUkSp2Eis28eUBcg==|W0EPaHwhmlQ+hsxB|VE5eOZ4No8n+Z6uj5r07TTMH24vDFqVHdUlYvkr3ccuV|VUmFyNzXec/95yriVt0TdSu88pWBiiRGc2lw/Q==|VkqGy9/Uesz+5CnhVd4Qdii/8ZaCiSdFfGZ/8g==|V03DpAMIO/mdDJnVJqUbR37mqI46MQKAxFVbU+d80rqLEd31gDO1D1E=|UEqH4PQg9pyusn4TB4ROJhOKRy9KwSNRaPER9iKZQykchUiApS6Q9s/THTVgvDpiUGAqpw==|UU2BzNiU70k/jZCfpjL9P0p85sB0oH4eLLs10odjza2AElg/OpknTXdHXg==|UkiEzHjLZQk7rCPrX9wecl9FyyOXBNa+k4kGYWTPYQM1K+cPitETdSs=',
        }
        result = self.web.submit_url(url, data)
        print self.web.url
        


def main():
    app = TaobaoWeb('ttwaitttwait', 'TTwait846266')
    app.login()

if __name__ == '__main__':
    main()
