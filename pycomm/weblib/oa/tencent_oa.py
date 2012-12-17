#! /usr/bin/env python2.6
#from SOAPpy import SOAPProxy
from py3rd.SOAPpy import SOAPProxy
#WSDLFILE='passportservice.asmx.xml'
WSDLFILE='http://passport.oa.com/services/passportservice.asmx?WSDL'
from datetime import datetime
import re
from pycomm.log import log


class oa():
    def __init__(self):
        self.ns='http://indigo.oa.com/services/'
        self._server=SOAPProxy(WSDLFILE,namespace=self.ns)
        self.userid=0
        self.username=''
        self.expiration=None

        pass    
    def getuser(self,ticket):
        results=self._server._sa('%sDecryptTicket' % self.ns)._ns(self.ns).DecryptTicket(encryptedTicket=ticket)
        #results=self._server.DecryptTicket('1')
        #print results.__dict__
        if not results.__dict__.has_key('LoginName'):
            log.error('results not found LoginName %s', results)
            return -1
        #print "authorization succ"
        self.userid=results['StaffId']
        self.username=results['LoginName']
        self.expiration=self.strtime2datetime(results['Expiration'])
        if  self.user_expired():return -2
        return 0    

    def strtime2datetime(self,strtime):
        mo=re.match('^(....)-(..)-(..)T(..):(..):(..).*$',strtime)
        if mo:
            g=mo.groups()
            year=int(g[0])
            mon=int(g[1])
            day=int(g[2])
            hour=int(g[3])
            min=int(g[4])
            sec=int(g[5])
            t=datetime(year,mon,day,hour,min,sec)
            return t    
    def user_expired(self):    
        t=datetime.now()
        if self.expiration and t<self.expiration:return False
        return True

        
def main():
    o=oa()
    ticket='85D854305DBCB3C9058EF9FF4D63EE33885EDD96C5EC806A94D9B658DBE639D33512C0BF4042285C61A667DB195E1F7FF2A01CB3AD8B16690F11028E1936D54C57F428D2A2AEEF400E9B63044EBDD8B15BC21DE4E4F9FB0C81CAC13DF26B2494C23AFD0E1E485EB3E886B9699AA2AC7B085350E0A75D325BCC185676C805AE8E35BAC3D7730688469E9EB358D6BAD97768A4307B5AC46405C92A16145CDAEB14590DCDDDF428ACBF25AD4DFFF1A8A3B2FD790599E7C6EC2768E5BA93D981683B'
    ret =o.getuser(ticket)
    if ret==0:print "authorization user succ"
    print o.userid
    print o.username
    print o.expiration
    

if __name__=="__main__":
    main()
