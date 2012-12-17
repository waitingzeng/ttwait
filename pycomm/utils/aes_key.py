#!/usr/bin/python
#coding=utf8
import pyDes
import time
import base64
from pycomm.utils import text
from pycomm.log import log
import sys
import urllib
from Crypto.Cipher import AES


BLOCK_SIZE = 16

altchars = '_-'
# one-liner to sufficiently pad the text to be encrypted
pad = lambda s: s + text.rnd_letters((BLOCK_SIZE - len(s) % BLOCK_SIZE) % BLOCK_SIZE)

# one-liners to encrypt/encode and decrypt/decode a string
# encrypt with AES, encode with base64
EncodeAES = lambda c, s: base64.urlsafe_b64encode(c.encrypt(pad(s)))
DecodeAES = lambda c, e: c.decrypt(base64.urlsafe_b64decode(e))

class AESKey(object):
    prefix = 'mf'
    
    def __init__(self, key):
        self.key = key
        if AES:
            self.aes = AES.new(key)
        else:
            self.aes = None

    def encrypt(self, content):
        t = int(time.time() * 1000)
        s = '%s%s%s' % (self.prefix, t, content)
        sk = EncodeAES(self.aes, s)
        return sk.replace('=', '.')

    def decrypt(self, key):
        raw_key = key
        if not key:
            return 7, None
        key = str(key.replace('.', '='))
        try:
            s = DecodeAES(self.aes, key)
        except:
            log.exception()
            return 1, None
        log.trace("key %s decrypt %s", raw_key, s)
        try:
            if len(s) % BLOCK_SIZE != 0:
                return 8, None
            prefix, t, content = s[:2], s[2:15], s[15:]
            t = int(t) / 1000
        except:
            log.exception()
            return 2, None
        if prefix != self.prefix:
            return 3, None

        if t >= (time.time() + 3600):   #允许的时间误差
            return 5, None
        return 0, content
    
