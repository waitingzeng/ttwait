#! /usr/bin/env python
#coding=utf-8
passport_ticket = """<?xml version="1.0" encoding="UTF-8"?>
<Envelope xmlns="http://schemas.xmlsoap.org/soap/envelope/"
          xmlns:wsse="http://schemas.xmlsoap.org/ws/2003/06/secext"
          xmlns:saml="urn:oasis:names:tc:SAML:1.0:assertion"
          xmlns:wsp="http://schemas.xmlsoap.org/ws/2002/12/policy"
          xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
          xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/03/addressing"
          xmlns:wssc="http://schemas.xmlsoap.org/ws/2004/04/sc"
          xmlns:wst="http://schemas.xmlsoap.org/ws/2004/04/trust">
<Header>
  <ps:AuthInfo xmlns:ps="http://schemas.microsoft.com/Passport/SoapServices/PPCRL" Id="PPAuthInfo">
    <ps:HostingApp>{7108E71A-9926-4FCB-BCC9-9A9D3F32E423}</ps:HostingApp>
    <ps:BinaryVersion>4</ps:BinaryVersion>
    <ps:UIVersion>1</ps:UIVersion>
    <ps:Cookies></ps:Cookies>
    <ps:RequestParams>AQAAAAIAAABsYwQAAAAxMDMz</ps:RequestParams>
  </ps:AuthInfo>
  <wsse:Security>
    <wsse:UsernameToken Id="user">
      <wsse:Username>%(user)s</wsse:Username>
      <wsse:Password>%(password)s</wsse:Password>
    </wsse:UsernameToken>
  </wsse:Security>
</Header>
<Body>
  <ps:RequestMultipleSecurityTokens xmlns:ps="http://schemas.microsoft.com/Passport/SoapServices/PPCRL" Id="RSTS">
    <wst:RequestSecurityToken Id="RST0">
      <wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>
      <wsp:AppliesTo>
        <wsa:EndpointReference>
          <wsa:Address>http://Passport.NET/tb</wsa:Address>
        </wsa:EndpointReference>
      </wsp:AppliesTo>
    </wst:RequestSecurityToken>
    <wst:RequestSecurityToken Id="RST1">
      <wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>
      <wsp:AppliesTo>
        <wsa:EndpointReference>
          <wsa:Address>messengerclear.live.com</wsa:Address>
        </wsa:EndpointReference>
      </wsp:AppliesTo>
      <wsse:PolicyReference URI="%(passport_policy)s"></wsse:PolicyReference>
    </wst:RequestSecurityToken>
    <wst:RequestSecurityToken Id="RST2">
      <wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>
      <wsp:AppliesTo>
        <wsa:EndpointReference>
          <wsa:Address>messenger.msn.com</wsa:Address>
        </wsa:EndpointReference>
      </wsp:AppliesTo>
      <wsse:PolicyReference URI="?id=507"></wsse:PolicyReference>
    </wst:RequestSecurityToken>
    <wst:RequestSecurityToken Id="RST3">
      <wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>
      <wsp:AppliesTo>
        <wsa:EndpointReference>
          <wsa:Address>contacts.msn.com</wsa:Address>
        </wsa:EndpointReference>
      </wsp:AppliesTo>
      <wsse:PolicyReference URI="MBI"></wsse:PolicyReference>
    </wst:RequestSecurityToken>
    <wst:RequestSecurityToken Id="RST4">
      <wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>
      <wsp:AppliesTo>
        <wsa:EndpointReference>
          <wsa:Address>messengersecure.live.com</wsa:Address>
        </wsa:EndpointReference>
      </wsp:AppliesTo>
      <wsse:PolicyReference URI="MBI_SSL"></wsse:PolicyReference>
    </wst:RequestSecurityToken>
    <wst:RequestSecurityToken Id="RST5">
      <wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>
      <wsp:AppliesTo>
        <wsa:EndpointReference>
          <wsa:Address>sup.live.com</wsa:Address>
        </wsa:EndpointReference>
      </wsp:AppliesTo>
      <wsse:PolicyReference URI="MBI"></wsse:PolicyReference>
    </wst:RequestSecurityToken>
    <wst:RequestSecurityToken Id="RST6">
      <wst:RequestType>http://schemas.xmlsoap.org/ws/2004/04/security/trust/Issue</wst:RequestType>
      <wsp:AppliesTo>
        <wsa:EndpointReference>
          <wsa:Address>storage.msn.com</wsa:Address>
        </wsa:EndpointReference>
      </wsp:AppliesTo>
      <wsse:PolicyReference URI="MBI"></wsse:PolicyReference>
    </wst:RequestSecurityToken>
  </ps:RequestMultipleSecurityTokens>
</Body>
</Envelope>"""


get_membership_list = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Header>
    <ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook">
      <ApplicationId>%(application_id)s</ApplicationId>
      <IsMigration>false</IsMigration>
      <PartnerScenario>Initial</PartnerScenario>
      <CacheKey />
      <BrandId>MSFT</BrandId>
    </ABApplicationHeader>
    <ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook">
      <ManagedGroupRequest>false</ManagedGroupRequest>
      <TicketToken>%(contact_ticket)s</TicketToken>
    </ABAuthHeader>
  </soap:Header>
  <soap:Body>
    <FindMembership xmlns="http://www.msn.com/webservices/AddressBook">
      <serviceFilter>
        <Types>
          <ServiceType>Messenger</ServiceType>
          <ServiceType>IMAvailability</ServiceType>
        </Types>
      </serviceFilter>
      <View>Full</View>
      <lastChange>0001-01-01T00:00:00.0000000</lastChange>
    </FindMembership>
  </soap:Body>
</soap:Envelope>"""

#get_membership_list = """<?xml version="1.0" encoding="utf-8"?>
#<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
#               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
#               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
#               xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
#<soap:Header>
#    <ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook">
#        <ApplicationId>%(application_id)s</ApplicationId>
#        <IsMigration>false</IsMigration>
#        <PartnerScenario>Initial</PartnerScenario>
#    </ABApplicationHeader>
#    <ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook">
#        <ManagedGroupRequest>false</ManagedGroupRequest>
#        <TicketToken>%(contact_ticket)s</TicketToken>
#    </ABAuthHeader>
#</soap:Header>
#<soap:Body>
#    <FindMembership xmlns="http://www.msn.com/webservices/AddressBook">
#        <serviceFilter>
#            <Types>
#                <ServiceType>Messenger</ServiceType>
#                <ServiceType>Invitation</ServiceType>
#                <ServiceType>SocialNetwork</ServiceType>
#                <ServiceType>Space</ServiceType>
#                <ServiceType>Profile</ServiceType>
#                <ServiceType>IMAvailability</ServiceType>
#            </Types>
#        </serviceFilter>
#        <View>Full</View>
#        <lastChange>0001-01-01T00:00:00.0000000</lastChange>
#        
#    </FindMembership>
#</soap:Body>
#</soap:Envelope>"""


get_oim_maildata = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<soap:Header>
  <PassportCookie xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi">
    <t>%(t)s</t>
    <p>%(p)s</p>
  </PassportCookie>
</soap:Header>
<soap:Body>
  <GetMetadata xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi" />
</soap:Body>
</soap:Envelope>"""


get_oim_message = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<soap:Header>
  <PassportCookie xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi">
    <t>%(t)s</t>
    <p>%(p)s</p>
  </PassportCookie>
</soap:Header>
<soap:Body>
  <GetMessage xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi">
    <messageId>%(msgid)s</messageId>
    <alsoMarkAsRead>false</alsoMarkAsRead>
  </GetMessage>
</soap:Body>
</soap:Envelope>"""


del_oim_message = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
<soap:Header>
  <PassportCookie xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi">
    <t>%(t)s</t>
    <p>%(p)s</p>
  </PassportCookie>
</soap:Header>
<soap:Body>
  <DeleteMessages xmlns="http://www.hotmail.msn.com/ws/2004/09/oim/rsi">
    <messageIds>
      <messageId>%(msgid)s</messageId>
    </messageIds>
  </DeleteMessages>
</soap:Body>
</soap:Envelope>"""



add_wlm_contact = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:xsd="http://www.w3.org/2001/XMLSchema"
           xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
<soap:Header>
<ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook">
    <ApplicationId>%(application_id)s</ApplicationId>
    <IsMigration>false</IsMigration>
    <PartnerScenario>ContactSave</PartnerScenario>
</ABApplicationHeader>
<ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook">
    <ManagedGroupRequest>false</ManagedGroupRequest>
    <TicketToken>%(contact_ticket)s</TicketToken>
</ABAuthHeader>
</soap:Header>
<soap:Body>
<ABContactAdd xmlns="http://www.msn.com/webservices/AddressBook">
    <abId>00000000-0000-0000-0000-000000000000</abId>
    <contacts>
        <Contact xmlns="http://www.msn.com/webservices/AddressBook">
            <contactInfo>
                <contactType>LivePending</contactType>
                <passportName>%(email)s</passportName>
                <isMessengerUser>true</isMessengerUser>
                <MessengerMemberInfo>
                    <DisplayName>%(displayName)s</DisplayName>
                </MessengerMemberInfo>
            </contactInfo>
        </Contact>
    </contacts>
    <options>
        <EnableAllowListManagement>true</EnableAllowListManagement>
    </options>
</ABContactAdd>
</soap:Body>
</soap:Envelope>"""



del_member_from_list_netword_1 = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:xsd="http://www.w3.org/2001/XMLSchema"
           xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
<soap:Header>
<ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook">
    <ApplicationId>%(application_id)s</ApplicationId>
    <IsMigration>false</IsMigration>
    <PartnerScenario>Timer</PartnerScenario>
</ABApplicationHeader>
<ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook">
    <ManagedGroupRequest>false</ManagedGroupRequest>
    <TicketToken>%(contact_ticket)s</TicketToken>
</ABAuthHeader>
</soap:Header>
<soap:Body>
<DeleteMember xmlns="http://www.msn.com/webservices/AddressBook">
    <serviceHandle>
        <Id>0</Id>
        <Type>Messenger</Type>
        <ForeignId></ForeignId>
    </serviceHandle>
    <memberships>
        <Membership>
            <MemberRole>%(member_role)s</MemberRole>
            <Members>
                <Member xsi:type="PassportMember" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <Type>%(member_type)s</Type>
                    <MembershipId>%(member_id)s</MembershipId>
                    <State>Accepted</State>
                </Member>
            </Members>
        </Membership>
    </memberships>
</DeleteMember>
</soap:Body>
</soap:Envelope>"""


del_member_from_list_netword_32 = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:xsd="http://www.w3.org/2001/XMLSchema"
           xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
<soap:Header>
<ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook">
    <ApplicationId>%(application_id)s</ApplicationId>
    <IsMigration>false</IsMigration>
    <PartnerScenario>ContactMsgrAPI</PartnerScenario>
</ABApplicationHeader>
<ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook">
    <ManagedGroupRequest>false</ManagedGroupRequest>
    <TicketToken>%(contact_ticket)s</TicketToken>
</ABAuthHeader>
</soap:Header>
<soap:Body>
<DeleteMember xmlns="http://www.msn.com/webservices/AddressBook">
    <serviceHandle>
        <Id>0</Id>
        <Type>Messenger</Type>
        <ForeignId></ForeignId>
    </serviceHandle>
    <memberships>
        <Membership>
            <MemberRole>%(member_role)s</MemberRole>
            <Members>
                <Member xsi:type="EmailMember" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <Type>Email</Type>
                    <MembershipId>%(member_id)s</MembershipId>
                    <State>Accepted</State>
                </Member>
            </Members>
        </Membership>
    </memberships>
</DeleteMember>
</soap:Body>
</soap:Envelope>"""



add_member_to_role_network_1 = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:xsd="http://www.w3.org/2001/XMLSchema"
           xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
<soap:Header>
<ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook">
    <ApplicationId>%(application_id)s</ApplicationId>
    <IsMigration>false</IsMigration>
    <PartnerScenario>ContactMsgrAPI</PartnerScenario>
</ABApplicationHeader>
<ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook">
    <ManagedGroupRequest>false</ManagedGroupRequest>
    <TicketToken>%(contact_ticket)s</TicketToken>
</ABAuthHeader>
</soap:Header>
<soap:Body>
<AddMember xmlns="http://www.msn.com/webservices/AddressBook">
    <serviceHandle>
        <Id>0</Id>
        <Type>Messenger</Type>
        <ForeignId></ForeignId>
    </serviceHandle>
    <memberships>
        <Membership>
            <MemberRole>%(member_role)s</MemberRole>
            <Members>
                <Member xsi:type="PassportMember" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <Type>Passport</Type>
                    <State>Accepted</State>
                    <PassportName>%(email)s</PassportName>
                </Member>
            </Members>
        </Membership>
    </memberships>
</AddMember>
</soap:Body>
</soap:Envelope>"""

add_member_to_role_network_32 = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns:xsd="http://www.w3.org/2001/XMLSchema"
           xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
<soap:Header>
<ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook">
    <ApplicationId>%(application_id)s</ApplicationId>
    <IsMigration>false</IsMigration>
    <PartnerScenario>ContactMsgrAPI</PartnerScenario>
</ABApplicationHeader>
<ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook">
    <ManagedGroupRequest>false</ManagedGroupRequest>
    <TicketToken>%(contact_ticket)s</TicketToken>
</ABAuthHeader>
</soap:Header>
<soap:Body>
<AddMember xmlns="http://www.msn.com/webservices/AddressBook">
    <serviceHandle>
        <Id>0</Id>
        <Type>Messenger</Type>
        <ForeignId></ForeignId>
    </serviceHandle>
    <memberships>
        <Membership>
            <MemberRole>%(member_role)s</MemberRole>
            <Members>
                <Member xsi:type="EmailMember" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    <Type>Email</Type>
                    <State>Accepted</State>
                    <Email>%(email)s</Email>
                    <Annotations>
                        <Annotation>
                            <Name>MSN.IM.BuddyType</Name>
                            <Value>32:YAHOO</Value>
                        </Annotation>
                    </Annotations>
                </Member>
            </Members>
        </Membership>
    </memberships>
</AddMember>
</soap:Body>
</soap:Envelope>"""



full_contact = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">
	<soap:Header>
		<ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook">
			<ApplicationId>%(application_id)s</ApplicationId>
			<IsMigration>false</IsMigration>
			<PartnerScenario>Initial</PartnerScenario>
		</ABApplicationHeader>
        <ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook">
            <ManagedGroupRequest>false</ManagedGroupRequest>
            <TicketToken>%(contact_ticket)s</TicketToken>
        </ABAuthHeader>		
	</soap:Header>
	<soap:Body>
        <ABFindContactsPaged xmlns="http://www.msn.com/webservices/AddressBook">
              <filterOptions>
                <DeltasOnly>false</DeltasOnly>
                <ContactFilter>
                  <IncludeHiddenContacts>true</IncludeHiddenContacts>
                  <IncludeShellContacts>true</IncludeShellContacts>
                </ContactFilter>
              </filterOptions>
              <abView>MessengerClient8</abView>
              <extendedContent>AB AllGroups CircleResult</extendedContent>
            </ABFindContactsPaged>		
	</soap:Body>
</soap:Envelope>"""


del_contact = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Header>
    <ABApplicationHeader xmlns="http://www.msn.com/webservices/AddressBook">
      <ApplicationId>%(application_id)s</ApplicationId>
      <IsMigration>false</IsMigration>
      <PartnerScenario>BlockUnblock</PartnerScenario>
    </ABApplicationHeader>
    <ABAuthHeader xmlns="http://www.msn.com/webservices/AddressBook">
      <ManagedGroupRequest>false</ManagedGroupRequest>
      <TicketToken>%(contact_ticket)s</TicketToken>
    </ABAuthHeader>
  </soap:Header>
  <soap:Body>
    <ABContactDelete xmlns="http://www.msn.com/webservices/AddressBook">
        <abId>
            00000000-0000-0000-0000-000000000000
        </abId>
        <contacts>
            <Contact>
                <contactId>
                    %(contact_id)s
                </contactId>
            </Contact>
        </contacts>
    </ABContactDelete>
  </soap:Body>
</soap:Envelope>"""


def get_xml(name, **kwargs):
    return globals()[name] % kwargs


if __name__ == '__main__':
    print get_xml('del_oim_message', t=1, p=1, msgid=1)
