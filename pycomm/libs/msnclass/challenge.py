# -*- coding: utf-8 -*-
import hashlib
import struct


PRODUCT_ID = "PROD0114ES4Z%Q5W"
PRODUCT_KEY = "PK}_A_0N_K%O?A9S"
CHL_MAGIC_NUM = 0x0E79A9C1


def _msn_challenge(data):
    """
    Compute an answer for MSN Challenge from a given data

        @param data: the challenge string sent by the server
        @type data: string
    """
    
    def little_endify(value, c_type="L"):
        """Transform the given value into little endian"""
        return struct.unpack(">" + c_type, struct.pack("<" + c_type, value))[0]

    md5_digest = hashlib.md5(data + PRODUCT_KEY).digest()
    # Make array of md5 string ints
    md5_integers = struct.unpack("<llll", md5_digest)
    md5_integers = [(x & 0x7fffffff) for x in md5_integers]
    # Make array of chl string ints
    data += PRODUCT_ID
    amount = 8 - len(data) % 8
    data += "".zfill(amount)
    chl_integers = struct.unpack("<%di" % (len(data)/4), data)
    # Make the key
    high = 0
    low = 0
    i = 0
    while i < len(chl_integers) - 1:
        temp = chl_integers[i]
        temp = (CHL_MAGIC_NUM * temp) % 0x7FFFFFFF
        temp += high
        temp = md5_integers[0] * temp + md5_integers[1]
        temp = temp % 0x7FFFFFFF
        high = chl_integers[i + 1]
        high = (high + temp) % 0x7FFFFFFF
        high = md5_integers[2] * high + md5_integers[3]
        high = high % 0x7FFFFFFF
        low = low + high + temp
        i += 2
    high = little_endify((high + md5_integers[1]) % 0x7FFFFFFF)
    low = little_endify((low + md5_integers[3]) % 0x7FFFFFFF)
    key = (high << 32L) + low
    key = little_endify(key, "Q")
    longs = [x for x in struct.unpack(">QQ", md5_digest)]
    longs = [little_endify(x, "Q") for x in longs]
    longs = [x ^ key for x in longs]
    longs = [little_endify(abs(x), "Q") for x in longs]
    out = ""
    for value in longs:
        value = hex(long(value))
        value = value[2:-1]
        value = value.zfill(16)
        out += value.lower()
    return out

if __name__ == '__main__':
    print _msn_challenge('15570131571988941333', "PROD0114ES4Z%Q5W", "PK}_A_0N_K%O?A9S", 0x0E79A9C1)