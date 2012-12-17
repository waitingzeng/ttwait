from text import get_in, get_in_list
import cgi
import urllib
import re
import htmlentitydefs

def get_hidden(page):
    return get_input(page)

def get_input(page, type='hidden'):
    data = {}
    for input in get_in_list(page, '<input', '>'):
        input = input.replace("'", '"')
        if input.lower().find('type="%s"' % type) == -1:
            continue
        name = get_in(input, 'name="', '"')
        value = get_in(input, 'value="', '"')
        if name is None:
            name = get_in(input, 'name=', ' ')
            if name is None:
                continue
            continue
        if value is None:
            value = get_in(input, 'value=', ' ')
            if value is None:
                value = ''
        data[name] = value
    return data


def get_tag(data, tag):
    btag = '<%s>' % tag
    etag = '</%s>' % tag
    return get_in(data, btag, etag)
    

def get_end_tag(data, tag):
    btag = '<%s' % tag.lower()
    etag = '</%s>' % tag.lower()
    data1 = data.lower()
    begin = 0
    while True:
        end = data1.find(etag, begin)
        if data1.find(btag, begin, end) != -1:
            begin = end+1
        else:
            return data[:end]

def escape(html):
    """Returns the given HTML with ampersands, quotes and carets encoded."""
    #('&', '&amp;')
    for k, v in [('<', '&lt;'), ('>', '&gt;'), ('  ', '&nbsp;&nbsp;'),]:
        html = html.replace(k, v)

    return html

def unescape(html):
    """Returns the given HTML with ampersands, quotes and carets encoded."""
    return html.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&nbsp;', ' ')




def not_html_tags(htmlText, repl=' '):
    return re.sub(r"<[^>]*>", repl, htmlText)



def urlencode(query):
    s = []
    for k,v in query:
        s.append('%s=%s' % (k, urllib.quote_plus(v)))
    return '&'.join(s)

cre = re.compile('&#(\d+);', re.I|re.M)
def iso_to_char(query):
    def f(match):
        a = match.group(1)
        if a.isdigit():
            a = int(a)
            if a <= 255:
                if a > 127:
                    return ''
                return chr(a)
            else:
                return eval('u"\u%x"' % a)
        return a
    return cre.sub(f, query)



def html_entity_decode(text):
     """
     Removes HTML or XML character references and entities from a text string.
       
     @param text The HTML (or XML) source text.
     @return The plain text, as a Unicode string, if necessary.
     """
     
     def fixup(m):
         text = m.group( 0 )
         if text[:2] == "&#" :
             # character reference
             try :
                 if text[: 3 ] == "&#x" :
                     return unichr ( int (text[ 3 : - 1 ], 16 ))
                 else :
                     return unichr ( int (text[ 2 : - 1 ]))
             except ValueError:
                 pass
         else :
             # named entity
             try :
                 text = unichr (htmlentitydefs.name2codepoint[text[ 1 : - 1 ]])
             except KeyError:
                 pass
         return text # leave as is
     return re.sub( "&#?/w+;" , fixup, text)



def htmlspecialchars(s):
    if not s or not isinstance(s, str):
        return s
    return cgi.escape(s)


def str_to_bool(s):
    if s.lower() == 'false':
        return False
    return True

def add_querystr(url, param):
    if not param:
        return url
    if url.endswith('?') or url.endswith('&'):
        return url + param
    if url.find('?') == -1:
        return url + '?' + param
    return url + '&' + param

class TString(str):
    def get_tag(self, tag):
        return get_tag(self, tag)
    
    def get_int(self, tag):
        return int(self.get_tag(tag))

    def get_bool(self, tag):
        return str_to_bool(self.get_tag(tag))

    def get_tags(self, tag):
        return list(get_in_list(self, '<%s>' % tag, '</%s>' % tag))

    def get_datetime(self, tag):
        return self.get_tag(tag)

