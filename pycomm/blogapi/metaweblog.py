
__version__ = "0.1"
import xmlrpclib
import sys
from xml.dom.minidom import parseString

#--------------------------------------
# About MetaWeblogAPI
# Reference http://www.xmlrpc.com/metaWeblogApi
#
# 1. entry point
# 1.1 newPost (blogid, username, password, struct, publish) returns string
# 1.2 editPost(postid, username, password, struct, publish) returns true
# 1.3 getPost (postid, username, password) returns struct
#
# 2. struct
# same with element in RSS 2.0
#   -----------------------------------------------------
#   Element      Description            Example
#   -----------------------------------------------------
#   title       The title of item   Venice Film Festival
#   link        The URL of the item http://nytimes.com/2004/12/07FEST.html
#   description The item synopsis   contents (in Blog API)
#   author      Email address       oprah\@oxygen.net
#   category    
#   comments
#   enclosure   Describes a media object
#               that is attached to the item
#   guid        A string that uniquely 
#               itentifies the item
#   pubData     published data
#   source      The RSS channel that the item
#                came from
# 
# ****** In python, struct is dictionary ***********
#   key             Example
# -------------------------------------------------
#   permaLink       http://sunshout.cafe24.com/blog/
#   description     blala
#   title
#   mt_excerpt
#   userid
#   datePosted     <DateTime ''19700101T00:00:00' at 22f698>
#   content
#   link
#   mt_allow_comments
#   dateCreated
#   postid
#   dateModified
#   categories    
#   mt_allow_pings
#
#  To Do List
#  1) explain struct
#

class MetaWeblog(object):
    def __init__(self, user, psw, xmlrpcurl, blogid=''):
        self.user, self.psw, self.xmlrpcurl = user, psw, xmlrpcurl
        self.blogid = blogid
        self.server = xmlrpclib.Server(xmlrpcurl).metaWeblog
        

    #---------------------------------------
    # change channel in rss2.0 to struct
    # 
    # channel           -->    struct
    # --------------------------------
    # channel:title            title
    # item:title               description:head
    # item:link                description:link
    # item:description         description:content
    #
    #
    # parameter
    #   channel : XML string
    def channel2struct(self, channel):
        
        root = parseString(channel)
        struct = {}
        #-----------
        # title
        #-----------
        t_title = root.getElementsByTagName('title')[0].firstChild.data
        struct['title'] = t_title.encode('utf-8')

        #--------------
        # description
        #--------------
        result = ''
        n_item = root.getElementsByTagName('item')
        for index in n_item:
            t_head = index.getElementsByTagName('title')[0].firstChild.data
            t_link = index.getElementsByTagName('link')[0].firstChild.data
            t_content = index.getElementsByTagName('description')[0].firstChild.data
            result = result \
                     + "<a href=" + t_link + " target=_blank_>" \
                     + t_head + "</a><br>"\
                     + t_content + "<br><br>"

        struct['description'] = result.encode('utf-8')

        return struct

    #----------------------------------
    # new post
    #----------------------------------
    def new_post(self, title, categories, description):
        """Post an entry on webblog site."""
        struct = {
            "title":title, 
            "categories":isinstance(categories, list) and categories or [categories],
            "description":description
        }
        
        postid = self.server.newPost(self.blogid, self.user, self.psw, struct, True)
        return postid
        
    #-------------------------------------
    # edit post
    #-------------------------------------
    def edit_post(self, postid, title, categories, description, publish=True):
        """Edit an existed entry """
        
        struct = {
            "title":title, 
            "categories":isinstance(categories, list) and categories or [categories],
            "description":description
        }
        # "description":publish(args[3])}
        # editPost(postId, username, password,
        #          {title, description, categories}, publish)
        ret = self.server.editPost(postid, self.user, self.psw, struct, publish)
        return ret
    
    #-------------------------------------
    # get post
    #-------------------------------------
    def get_post(self, postid):
        """get an post from args
        args = post number
        """
        # getPost(postid, username, password)
        # return struct
        struct = self.server.getPost(postid, self.user, self.psw)
        return struct

    #----------------------------------------
    # get categories if exist
    #----------------------------------------
    def get_categorylist(self):
        """get categories if exist"""
        # getCategories(blogid, username, password)
        # return list of struct
        # struct = {description, htmlURL, rssURL element}
        category_list = self.server.getCategories(self.blogid, self.user, self.psw)
        return category_list

    #----------------------------------------
    # attach media object
    #----------------------------------------
    def new_mediaobject(self, postid, name, type, bits):
        """Upload an multimedia to blog site."""
        
        struct = {"name":name, "type":type, "bits":bits}
        # newMediaObject(postId, username, password,
        #                {name, type, bits})
        upload = self.server.newMediaObject(postid, self.user, self.psw, struct)
        return upload['url']
    

    def get_recentposts(self, num):
        """Get recently posted entries."""

        # getRecentPosts(blogid, username, password, numposts)
        posts = self.server.getRecentPosts(self.blogid, self.user, self.psw, num)
        return posts


if __name__ == "__main__":
    import random
    blog = MetaWeblog('ttwait', 'TTwait846266', 'http://www.money988.com/xml-rpc/index.asp')
    cats = blog.get_categorylist()
    print cats
    cat = random.choice(cats)
    
    mytitle = 'Automatic Fund crawler'
    mycategories = cat['title']
    mytext = """
<b>some contents</b>
html does not work
<h1>test</h1>
"""
    print blog.new_post(mytitle, mycategories, mytext)
    