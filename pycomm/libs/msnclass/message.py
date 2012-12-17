#! /usr/bin/env python
#coding=utf-8

# the message length (include header) is limited (maybe since WLM 8.5 released)
# for WLM: 1664 bytes
# for YIM: 518 bytes
# for OIM: 573 bytes

max_msn_message_len = 1664
max_yahoo_message_len = 518
max_oim_message_len = 573


def get_message(message, network = 1, is_oim = True):
    if is_oim:
        oim_header = "Dest-Agent: client\r\n"
    else:
        oim_header = ''
    msg_header = "MIME-Version: 1.0\r\nContent-Type: text/plain; charset=UTF-8\r\nX-MMS-IM-Format: FN=Arial; EF=; CO=0; CS=1; PF=0\r\n%s\r\n" % oim_header
    msg_header_len = len(msg_header)
    if network == 1:
        if is_oim:
            maxlen = max_oim_message_len - msg_header_len
        else:
            maxlen = max_msn_message_len - msg_header_len
    else:
        maxlen = max_yahoo_message_len - msg_header_len
        
    msg = message[:maxlen]
    msg = msg.encode('gbk')
    return msg_header + msg
    