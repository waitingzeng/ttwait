#! /usr/bin/env python
#coding=utf-8
from pycomm.log import log
from pycomm.utils.storage import Storage
from pycomm.utils.html import html_entity_decode
import re

# no Redurect faultcode or URL
# we should get the ticket here

# we need ticket and secret code
# RST1: messengerclear.live.com
# <wsse:BinarySecurityToken Id="Compact1">t=tick&p=</wsse:BinarySecurityToken>
# <wst:BinarySecret>binary secret</wst:BinarySecret>
# RST2: messenger.msn.com
# <wsse:BinarySecurityToken Id="PPToken2">t=tick</wsse:BinarySecurityToken>
# RST3: contacts.msn.com
# <wsse:BinarySecurityToken Id="Compact3">t=tick&p=</wsse:BinarySecurityToken>
# RST4: messengersecure.live.com
# <wsse:BinarySecurityToken Id="Compact4">t=tick&p=</wsse:BinarySecurityToken>
# RST5: sup.live.com
# <wsse:BinarySecurityToken Id="Compact5">t=tick&p=</wsse:BinarySecurityToken>
# RST6: storage.msn.com
# <wsse:BinarySecurityToken Id="Compact6">t=tick&p=</wsse:BinarySecurityToken>
tickets_re_1 = re.compile(r"<wsse\:BinarySecurityToken Id=\"Compact1\">(.*)</wsse\:BinarySecurityToken>(.*)" +
           "<wst\:BinarySecret>(.*)</wst\:BinarySecret>(.*)" +
           "<wsse\:BinarySecurityToken Id=\"PPToken2\">(.*)</wsse\:BinarySecurityToken>(.*)" +
           "<wsse\:BinarySecurityToken Id=\"Compact3\">(.*)</wsse\:BinarySecurityToken>(.*)" +
           "<wsse\:BinarySecurityToken Id=\"Compact4\">(.*)</wsse\:BinarySecurityToken>(.*)" +
           "<wsse\:BinarySecurityToken Id=\"Compact5\">(.*)</wsse\:BinarySecurityToken>(.*)" + 
           "<wsse\:BinarySecurityToken Id=\"Compact6\">(.*)</wsse\:BinarySecurityToken>(.*)")


# Since 2011/2/15, the return value will be Compact2, not PPToken2

# we need ticket and secret code
# RST1: messengerclear.live.com
# <wsse:BinarySecurityToken Id="Compact1">t=tick&p=</wsse:BinarySecurityToken>
# <wst:BinarySecret>binary secret</wst:BinarySecret>
# RST2: messenger.msn.com
# <wsse:BinarySecurityToken Id="PPToken2">t=tick</wsse:BinarySecurityToken>
# RST3: contacts.msn.com
# <wsse:BinarySecurityToken Id="Compact3">t=tick&p=</wsse:BinarySecurityToken>
# RST4: messengersecure.live.com
# <wsse:BinarySecurityToken Id="Compact4">t=tick&p=</wsse:BinarySecurityToken>
# RST5: sup.live.com
# <wsse:BinarySecurityToken Id="Compact5">t=tick&p=</wsse:BinarySecurityToken>
# RST6: storage.msn.com
# <wsse:BinarySecurityToken Id="Compact6">t=tick&p=</wsse:BinarySecurityToken>
tickets_re_2 = re.compile("<wsse\:BinarySecurityToken Id=\"Compact1\">(.*)</wsse\:BinarySecurityToken>(.*)" +
           "<wst\:BinarySecret>(.*)</wst\:BinarySecret>(.*)" +
           "<wsse\:BinarySecurityToken Id=\"Compact2\">(.*)</wsse\:BinarySecurityToken>(.*)" +
           "<wsse\:BinarySecurityToken Id=\"Compact3\">(.*)</wsse\:BinarySecurityToken>(.*)" +
           "<wsse\:BinarySecurityToken Id=\"Compact4\">(.*)</wsse\:BinarySecurityToken>(.*)" +
           "<wsse\:BinarySecurityToken Id=\"Compact5\">(.*)</wsse\:BinarySecurityToken>(.*)" +
           "<wsse\:BinarySecurityToken Id=\"Compact6\">(.*)</wsse\:BinarySecurityToken>(.*)")




def get_tickets(data):
    
    matches = tickets_re_1.search(data)
    # no ticket found!
    if not matches:
        matches = tickets_re_2.search(data)
        # no ticket found!
        if not matches:
            log.debug("*** Can't get passport ticket!")
            return False
        
    

    #self.debug_message(var_export($matches, True))
    # matches[0]: all data
    # matches[1]: RST1 (messengerclear.live.com) ticket
    # matches[2]: ...
    # matches[3]: RST1 (messengerclear.live.com) binary secret
    # matches[4]: ...
    # matches[5]: RST2 (messenger.msn.com) ticket
    # matches[6]: ...
    # matches[7]: RST3 (contacts.msn.com) ticket
    # matches[8]: ...
    # matches[9]: RST4 (messengersecure.live.com) ticket
    # matches[10]: ...
    # matches[11]: RST5 (sup.live.com) ticket
    # matches[12]: ...
    # matches[13]: RST6 (storage.live.com) ticket
    # matches[14]: ...

    # so
    # ticket => $matches[1]
    # secret => $matches[3]
    # web_ticket => $matches[5]
    # contact_ticket => $matches[7]
    # oim_ticket => $matches[9]
    # sup_ticket => $matches[11]
    # storage_ticket => $matches[13]

    # yes, we get ticket
    tickets = Storage({
                'ticket' : html_entity_decode(matches.group(1)),
                'secret' : html_entity_decode(matches.group(3)),
                'web_ticket' : html_entity_decode(matches.group(5)),
                'contact_ticket' : html_entity_decode(matches.group(7)),
                'oim_ticket' : html_entity_decode(matches.group(9)),
                'sup_ticket' : html_entity_decode(matches.group(11)),
                'storage_ticket' : html_entity_decode(matches.group(13))
                })
    #self.debug_message(var_export($aTickets, True))
    return tickets




if __name__ == '__main__':
    app = Storage()
    app.email = 'ljfygxi0151@hotmail.com'
    app.pwd = 'TTwait846266'
