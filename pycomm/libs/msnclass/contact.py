#! /usr/bin/env python
#coding=utf-8
from xml_content import get_xml
import re
import base64
import httplib
import traceback
from pycomm.utils.storage import Storage
from pycomm.utils.text import get_in, get_in_list
from pycomm.utils.html import get_tag
from pycomm.log import log
from pycomm.utils import mixin

membership_url = 'http://contacts.msn.com/abservice/SharingService.asmx'
#membership_url = 'https://proxy-bay.contacts.msn.com/abservice/SharingService.asmx'
membership_soap = 'http://www.msn.com/webservices/AddressBook/FindMembership'

addmember_url = 'https://contacts.msn.com/abservice/SharingService.asmx'
addmember_soap = 'http://www.msn.com/webservices/AddressBook/AddMember'

contact_url = 'https://contacts.msn.com/abservice/abservice.asmx'
add_contact_soap = 'http://www.msn.com/webservices/AddressBook/ABContactAdd'

del_contact_url = 'https://proxy-bay.contacts.msn.com/abservice/abservice.asmx'
del_contact_soap = 'http://www.msn.com/webservices/AddressBook/ABContactDelete'

full_contact_soap = 'http://www.msn.com/webservices/AddressBook/ABFindAll'

delmember_url = 'https://contacts.msn.com/abservice/SharingService.asmx'
delmember_soap = 'http://www.msn.com/webservices/AddressBook/DeleteMember'


class User(Storage):
    """User class, used to store your 'friends'"""
    def __init__(self, email = '', network = '', member_role='', membership_id = None):
        self.email = email
        if email:
            self.domain, self.name = email.split('@')
        else:
            self.domain, self.name = None, None
        self.network = network
        self.member_role = member_role
        self.membership_id = membership_id
        

    def parse(self, data):
        for x in ['MembershipId', 'Type', 'DisplayName', 'State', 'Deleted', 'LastChanged', 'JoinedDate', 'ExpirationDate', 'PassportName', 'IsPassportNameHidden', 'PassportId', 'CID', 'LookedupByCID']:
            value = get_tag(data, x)
            if not value:
                continue
            if value.isdigit():
                value = int(value)
            if value == 'true':
                value = True
            if value == 'false':
                value = False
            self[x.lower()] = value
            

    def __repr__(self):
        return '<user email:%s network:"%s" membership_id:%s>' % (self.email,
                self.network, self.membership_id)



def get_membership_list(self):
    try:
        return self.membership_list
    except:
        pass
    xml = self.get_xml('get_membership_list')
    
    try:
        data = self.get_page(membership_url, xml, SOAPAction=membership_soap)
    except Exception, info:
        #traceback.print_exc()
        log.error("%s get membership list error, code:%s, resp:\n%s", self.user, info.code, info.fp.read())
        return None
    #http_code, data, errstr = curl_exec(self.membership_url, xml, header_array)
    
    if not data:
        log.debug("%s *** get membership failed last code:%s", self.user, self.last_code)
        return None
    else:
        pass
        #log.debug("get membership data is %s", data)
    
    contact_list = []
    memberships = get_in_list(data, '<Membership>', '</Membership>')
    for membership in memberships:
        member_role = get_in(membership, '<MemberRole>', '</MemberRole>')
        if not member_role or member_role not in ['Allow', 'Reverse', 'Pending']:
            continue
        
        members = get_in_list(membership, '<Member ', '</Member>')
        
        for member in members:
            member_type = get_in(member, 'xsi:type="', '">')
            
            if not member_type:
                continue
            network = -1
            membership_id = get_in(member, '<MembershipId>', '</MembershipId>')
            if not membership_id:
                continue
            
            if member_type == 'PassportMember':
                if member.find('<Type>Passport</Type>') == -1:
                    continue
                network = 1
                email = get_in(member, '<PassportName>', '</PassportName>')
                
            elif member_type == 'EmailMember':
                if member.find('<Type>Email</Type>') == -1:
                    continue
                # Value is 32: or 32:YAHOO
                yahoo_net_work = get_in(member, '<Annotation><Name>MSN.IM.BuddyType</Name><Value>', '</Value></Annotation>')
                if not yahoo_net_work:
                    continue
                network = yahoo_net_work.split(':')[0]
                if int(network) != 32:
                    continue
                network = 32
                email = get_in(member, '<Email>', '</Email>')
            else:
                log.debug('unknow member type %s', member_type)
            if network == -1:
                continue
            if email:
                user = User(email, network, member_role, membership_id)
                user.parse(member)
                
                contact_list.append(user)
    
    self.membership_list = contact_list
    return contact_list
mixin.setMixin('msn', 'get_membership_list', get_membership_list)

def force_get_membership_list(self, num=3):
    for i in range(num):
        members = self.get_membership_list()
        if members is not None:
            return members
    return None
mixin.setMixin('msn', 'force_get_membership_list', force_get_membership_list)

def get_allow_email(self):
    members = self.force_get_membership_list()
    if members is None:
        log.error("%s force get memebership list fail", self.user)
        return None
    emails = set([x.email for x in members])
    return list(emails)
mixin.setMixin('msn', 'get_allow_email', get_allow_email)

def add_contact(self, email, network, display = '', sendADL = False):
    if network != 1:
        return True
    # add contact for WLM

    xml = self.get_xml('add_wlm_contact', displayName = display, email=email)

    try:
        data = self.get_page(contact_url, xml, SOAPAction=add_contact_soap)
    except Exception, info:
        errorcode = info.fp.read()
        if errorcode.find('QuotaLimitReached') != -1:
            return 1
        log.debug('add contact error code:%s, resp\n%s', info.code, info.fp.read())
        return -1
    if not data:
        log.debug('add contact %s fail', email)
        return -1

    if sendADL:
        u_name, u_domain = email.split('@')
        for l in [1,2]:
            s = '<ml l="1"><d n="%s"><c n="%s" l="%s" t="%s" /></d></ml>' % (u_domain, u_name, l, network)
        
            self._send('ADL', '%s\r\n%s' % (len(s), s), raw=1)
    return 0
mixin.setMixin('msn', 'add_contact', add_contact)

def del_member_from_role(self, member_id, network, member_role):
    if network not in [1, 32]:
        return True
    if not member_id:
        return True
   
    if network == 1:
        xml = self.get_xml('del_member_from_list_netword_1', member_id=member_id, member_role = member_role)
    else:
        xml = self.get_xml('del_member_from_list_netword_32', member_id=member_id, member_role = member_role)
    
    try:
        data = self.get_page(delmember_url, xml, SOAPAction=delmember_soap)
    except Exception, info:
        log.error('delete memeber from role error, code:%s, resp:\n%s', info.code, info.fp.read())
        return False

    if not data:
        log.debug('*** delete memeber (network:%s) %s from %s fail', network, member_id, member_role)
        return False
    log.debug(data)
    return True
mixin.setMixin('msn', 'del_member_from_role', del_member_from_role)

def add_member_to_role(self, email, network, member_role):
    if network not in [1,32]:
        return True
    
    if network == 1:
        xml = self.get_xml('add_member_to_role_network_1', email=email, member_role=member_role)
    else:
        xml = self.get_xml('add_member_to_role_network_32', email=email, member_role=member_role)
    try:
        
        data = self.get_page(addmember_url, xml, SOAPAction=addmember_soap)
    except Exception, info:
        log.error('add memeber to role error, code:%s resp:\n%s', info.code, info.fp.read())
        return False
    if not data:
        log.debug('add memeber fail')
        return False
    return True
mixin.setMixin('msn', 'add_member_to_role', add_member_to_role)


from ab import Group, Contact, ABResult
def get_full_addressbook(self):
    try:
        return self.address_books
    except:
        pass
    
    xml = self.get_xml('full_contact')
        
    try:
        data = self.get_page(contact_url, xml, SOAPAction=full_contact_soap)
    except Exception, info:
        log.error("%s get full addressbook list error, code:%s, resp:\n%s", self.user, info.code, info.fp.read())
        return []
    
    if not data:
        log.debug("%s *** get full contacts failed", self.user)
        return []
    groups = []
    contacts = []
    groups_tag = get_tag(data, 'groups')
    for group in get_in_list(groups_tag, '<Group>', '</Group>'):
        groups.append(Group(group))

    contact_tag = get_tag(data, 'contacts')
    for contact in get_in_list(contact_tag, '<Contact>', '</Contact>'):
        item = Contact(contact)
        if item.type == 'Me':
            continue
        contacts.append(item)
    
    address_book =  ABResult(contacts, groups) #FIXME: add support for the ab param
    self.address_books = address_book
    return address_book
mixin.setMixin('msn', 'get_full_addressbook', get_full_addressbook)


def del_contact(self, contact):
    xml = self.get_xml('del_contact', contact_id = contact.id)
    try:
        data = self.get_page(del_contact_url, xml, SOAPAction=del_contact_soap)
    except Exception, info:
        log.error("del contact error, code:%s, resp:\n%s", info.code, info.fp.read())
        return []
    
    if not data:
        log.debug("*** del contacts failed")
        return []
    
    if data.find('ABContactDeleteResponse') != -1:
        return True
    return False
mixin.setMixin('msn', 'del_contact', del_contact)
