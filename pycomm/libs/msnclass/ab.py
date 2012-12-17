#! /usr/bin/env python
#coding=utf-8
from pycomm.utils.html import  TString
from pycomm.utils.html import get_tag
class ABResult(object):
    """ABFindAll Result object"""
    def __init__(self, contacts, groups):
        self.contacts = contacts
        self.groups = groups
    
    def find_contact(self, email):
        for contact in self.contacts:
            if contact.passport_name == email:
                return contact
        return None

class Group(object):
    def __init__(self, group):
        group = TString(group)
        self.id = group.get_tag("groupId")

        group_info = TString(get_tag(group, "groupInfo"))
            
        self.type = group_info.get_tag("groupType")
        self.name = group_info.get_tag("name")
        self.is_not_mobile_visible = group_info.get_bool("IsNotMobileVisible")
        self.is_private = group_info.get_bool("IsPrivate")

        self.annotations = group_info.get_tag("Annotations")
        
        self.properties_changed = [] #FIXME: implement this
        self.deleted = group.get_bool("fDeleted")
        self.last_changed = group.get_bool("lastChange")

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return self.id == other.id

    def __repr__(self):
        return "<Group id=%s>" % self.id

class ContactEmail(object):
    def __init__(self, email):
        email = TString(email)
        self.type = email.get_tag("contactEmailType")
        self.email = email.get_tag("email")
        self.is_messenger_enabled = email.get_bool("isMessengerEnabled")
        self.capability = email.get_int("Capability")
        self.messenger_enabled_externally = email.get_bool("MessengerEnabledExternally")
        
    def __repr__(self):
        return str(self)
    
    def __str__(self):
        return 'Contact<%s>' % self.email

class ContactPhone(object):
    def __init__(self, phone):
        phone = TString(phone)
        self.type = phone.get_tag("contactPhoneType")
        self.number = phone.get_tag("number")
        self.is_messenger_enabled = phone.get_bool("isMessengerEnabled")
        self.properties_changed = phone.get_tag("propertiesChanged").split(' ')

class ContactLocation(object):
    def __init__(self, location):
        location = TString(location)
        self.type = location.get_tag("contactLocationType")
        self.name = location.get_tag("name")
        self.city = location.get_tag("city")
        self.country = location.get_tag("country")
        self.postal_code = location.get_tag("postalcode")
        self.changes = location.get_tag("Changes").split(' ')

class Contact(object):
    def __init__(self, contact):
        contact = TString(contact)
        self.id = contact.get_tag("contactId")

        contact_info = TString(contact.get_tag("contactInfo"))

        self.Groups = []
        groups = contact_info.get_tags("groupIds")
        if groups is not None:
            for group in groups:
                self.Groups.append(group)

        self.type = contact_info.get_tag("contactType")
        self.quick_name = contact_info.get_tag("quickName")
        self.passport_name = contact_info.get_tag("passportName")
        self.display_name = contact_info.get_tag("displayName")
        self.is_passport_name_hidden = contact_info.get_bool("IsPassportNameHidden")

        self.firstname = contact_info.get_tag("firstName")
        self.lastname = contact_info.get_tag("lastName")

        self.puid = contact_info.get_int("puid")
        self.cid = contact_info.get_int("CID")

        self.is_not_mobile_visible = contact_info.get_bool("IsNotMobileVisible")
        self.is_mobile_im_enabled = contact_info.get_bool("isMobileIMEnabled")
        self.is_messenger_user = contact_info.get_bool("isMessengerUser")
        self.is_favorite = contact_info.get_bool("isFavorite")
        self.is_smtp = contact_info.get_bool("isSmtp")
        self.has_space = contact_info.get_bool("hasSpace")

        self.spot_watch_state = contact_info.get_tag("spotWatchState")
        self.birthdate = contact_info.get_datetime("birthdate")

        self.primary_email_type = contact_info.get_tag("primaryEmailType")
        self.primary_location = contact_info.get_tag("PrimaryLocation")
        self.primary_phone = contact_info.get_tag("primaryPhone")

        self.is_private = contact_info.get_bool("IsPrivate")
        self.gender = contact_info.get_tag("Gender")
        self.time_zone = contact_info.get_tag("TimeZone")

        self.annotations = contact_info.get_tags("annotations")
        
        self.emails = []
        emails = contact_info.get_tags("emails")
        for contact_email in emails:
            self.emails.append(ContactEmail(contact_email))

        self.properties_changed = [] #FIXME: implement this
        self.deleted = contact.get_bool("fDeleted")
        self.last_changed = contact.get_datetime("lastChanged")


    def __str__(self):
        return '%s<%s>' % (self.emails, self.id)
