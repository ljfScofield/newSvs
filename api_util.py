#!/usr/env python
# -*- coding: utf-8 -*-

""" API related with inputdata.

The module provides utility functions for convinence.

__author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
__date__ = "Aug 2016"
__version__ = "0.1.0"

Copyright 2016 XH Smart Card Co,. Ltd

Author: wg@china-xinghan.com
"""

import binascii
import api_config


import smartcard.util


toBytes = smartcard.util.toBytes

a2b = binascii.a2b_hex


def b2a(b):
    return binascii.b2a_hex(b).upper()

def get_codecs():
    cfg = api_config.CONFIG
    options = cfg.options(__name__)
    return filter(lambda x:cfg.getboolean(__name__, x), options)

def u(s):
    if type(s)==type(u''):
        return s
    for codec in get_codecs():
        try:
            return s.decode(codec)
        except UnicodeDecodeError: 
            continue
    else:
        return u'中文decode失败'


def swap(s):
    l = len(s)
    if l%2:
        s1 = s[:-1]
        return ''.join([s1[i+1]+s1[i] for i in range(0,l-1,2)]) + s[-1]
    else:
        return ''.join([s[i+1]+s[i] for i in range(0,len(s),2)])


def verifyluhn(s):
    '''检查s的luhn校验值，参考 ISO/IEC 7812-1, Annex B
       https://en.wikipedia.org/wiki/Luhn_algorithm
    '''
    lst, total = map(int, s), 0
    for i, x in enumerate(lst[::-1]):
        if i>0:
            y = x
            if i&1:
                y = x*2
                if y>9:
                    y = y-9
            total += y
        else:
            pass # skip the check digit

    luhn1 = (total * 9) % 10
    luhn = int(s[-1])
    return luhn==luhn1


def utf8toascii(u8):
    return u8.decode('UTF-8').encode('ascii')


if __name__=='__main__':
    for x in ('79927398713', '5218990780271010', '6217907000008640938', '49927398716', '1234567812345670', '6226000001267504', '6226000003372401', '4135120060015720'):
        assert verifyluhn(x)
    for iccid in ('982520505191740038F4', ):
        assert verifyluhn(swap(iccid)[:-1])
    for iccid in ('98680076910062769559', ):
        assert not verifyluhn(iccid) # 部分老SIM卡的ICCID没有校验位

