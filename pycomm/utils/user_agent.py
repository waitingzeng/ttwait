import re

platforms =  {
     'windows nt 6.0'    : 'Windows Longhorn',
     'windows nt 5.2'    : 'Windows 2003',
     'windows nt 5.0'    : 'Windows 2000',
     'windows nt 5.1'    : 'Windows XP',
     'windows nt 4.0'    : 'Windows NT 4.0',
     'winnt4.0'          : 'Windows NT 4.0',
     'winnt 4.0'         : 'Windows NT',
     'winnt'             : 'Windows NT',
     'windows 98'        : 'Windows 98',
     'win98'             : 'Windows 98',
     'windows 95'        : 'Windows 95',
     'win95'             : 'Windows 95',
     'windows'           : 'Unknown Windows OS',
     'os x'              : 'Mac OS X',
     'ppc mac'           : 'Power PC Mac',
     'freebsd'           : 'FreeBSD',
     'ppc'               : 'Macintosh',
     'linux'             : 'Linux',
     'debian'            : 'Debian',
     'sunos'             : 'Sun Solaris',
     'beos'              : 'BeOS',
     'apachebench'       : 'ApacheBench',
     'aix'               : 'AIX',
     'irix'              : 'Irix',
     'osf'               : 'DEC OSF',
     'hp-ux'             : 'HP-UX',
     'netbsd'            : 'NetBSD',
     'bsdi'              : 'BSDi',
     'openbsd'           : 'OpenBSD',
     'gnu'               : 'GNU/Linux',
     'unix'              : 'Unknown Unix OS'
}


browsers = {
     'Flock'             : 'Flock',
     'Chrome'            : 'Chrome',
     'Opera'             : 'Opera',
     'MSIE'              : 'Internet Explorer',
     'Internet Explorer' : 'Internet Explorer',
     'Shiira'            : 'Shiira',
     'Firefox'           : 'Firefox',
     'Chimera'           : 'Chimera',
     'Phoenix'           : 'Phoenix',
     'Firebird'          : 'Firebird',
     'Camino'            : 'Camino',
     'Netscape'          : 'Netscape',
     'OmniWeb'           : 'OmniWeb',
     'Safari'            : 'Safari',
     'Mozilla'           : 'Mozilla',
     'Konqueror'         : 'Konqueror',
     'icab'              : 'iCab',
     'Lynx'              : 'Lynx',
     'Links'             : 'Links',
     'hotjava'           : 'HotJava',
     'amaya'             : 'Amaya',
     'IBrowse'           : 'IBrowse'
}

mobiles = {
     'mobileexplorer'    : 'Mobile Explorer',
     'palmsource'        : 'Palm',
     'palmscape'         : 'Palmscape',

     # Phones and Manufacturers
     'motorola'          : "Motorola",
     'nokia'             : "Nokia",
     'palm'              : "Palm",
     'iphone'            : "Apple iPhone",
     'ipad'              : "iPad",
     'ipod'              : "Apple iPod Touch",
     'sony'              : "Sony Ericsson",
     'ericsson'          : "Sony Ericsson",
     'blackberry'        : "BlackBerry",
     'cocoon'            : "O2 Cocoon",
     'blazer'            : "Treo",
     'lg'                : "LG",
     'amoi'              : "Amoi",
     'xda'               : "XDA",
     'mda'               : "MDA",
     'vario'             : "Vario",
     'htc'               : "HTC",
     'samsung'           : "Samsung",
     'sharp'             : "Sharp",
     'sie-'              : "Siemens",
     'alcatel'           : "Alcatel",
     'benq'              : "BenQ",
     'ipaq'              : "HP iPaq",
     'mot-'              : "Motorola",
     'playstation portable'  : "PlayStation Portable",
     'hiptop'            : "Danger Hiptop",
     'nec-'              : "NEC",
     'panasonic'         : "Panasonic",
     'philips'           : "Philips",
     'sagem'             : "Sagem",
     'sanyo'             : "Sanyo",
     'spv'               : "SPV",
     'zte'               : "ZTE",
     'sendo'             : "Sendo",

     # Operating Systems
     'symbian'               : "Symbian",
     'SymbianOS'             : "SymbianOS",
     'elaine'                : "Palm",
     'palm'                  : "Palm",
     'series60'              : "Symbian S60",
     'windows ce'            : "Windows CE",

     # Browsers
     'obigo'                 : "Obigo",
     'netfront'              : "Netfront Browser",
     'openwave'              : "Openwave Browser",
     'mobilexplorer'         : "Mobile Explorer",
     'operamini'             : "Opera Mini",
     'opera mini'            : "Opera Mini",

     # Other
     'digital paths'         : "Digital Paths",
     'avantgo'               : "AvantGo",
     'xiino'                 : "Xiino",
     'novarra'               : "Novarra Transcoder",
     'vodafone'              : "Vodafone",
     'docomo'                : "NTT DoCoMo",
     'o2'                    : "O2",

     # Fallback
     'mobile'                : "Generic Mobile",
     'wireless'              : "Generic Mobile",
     'j2me'                  : "Generic Mobile",
     'midp'                  : "Generic Mobile",
     'cldc'                  : "Generic Mobile",
     'up.link'               : "Generic Mobile",
     'up.browser'            : "Generic Mobile",
     'smartphone'            : "Generic Mobile",
     'cellphone'             : "Generic Mobile",
     'android'               : "Generic Mobile",
}

# There are hundreds of bots but these are the most common.
robots = {
     'googlebot'         : 'Googlebot',
     'msnbot'            : 'MSNBot',
     'slurp'             : 'Inktomi Slurp',
     'yahoo'             : 'Yahoo',
     'askjeeves'         : 'AskJeeves',
     'fastcrawler'       : 'FastCrawler',
     'infoseek'          : 'InfoSeek Robot 1.0',
     'lycos'             : 'Lycos'
}


class UserAgent(object):


    def __init__(self, agent):
        self.agent = agent.strip()
        self.agent_lower = self.agent.lower()
        self.platform = 'Unknown Platform'
        self.is_browser = False
        self.browser = ''
        self.is_robot = False
        self.robot = ''
        self.is_mobile = False
        self.mobile = ''
        self.is_weixin = self.agent.find('micromessenger') != -1
        self._compile_data()

    def _compile_data(self):
        self._set_platform()
        for func in ['_set_robot', '_set_browser', '_set_mobile']:
            if getattr(self, func)():
                break

    def _set_platform(self):
        for k, v in platforms.items():
            if self.agent_lower.find(k) != -1:
                self.platform = v
                return
        self.platform = 'Unknown Platform'

    def _set_browser(self):
        for k, v in browsers.items():
            if self.agent_lower.find(k.lower()) != -1:
                self.is_browser = True
                self.browser = v
                self._set_mobile()
                return True
        return False

    def _set_robot(self):
        for k, v in robots.items():
            if self.agent_lower.find(k.lower()) != -1:
                self.is_robot = True
                self.robot = v
                return True
        return False

    def _set_mobile(self):
        for k, v in mobiles.items():
            if self.agent_lower.find(k.lower()) != -1:
                self.is_mobile = True
                self.mobile = v
                return True
        return False

def main():
    user_agent = UserAgent('mozilla/5.0 (linux; u; android 4.1.1; zh-cn; galaxy nexus build/jro03c) applewebkit/534.30 (khtml, like gecko) version/4.0 mobile safari/534.30 micromessenger/4.3.215') 
    print user_agent.__dict__

if __name__ == '__main__':
    main()     

