#!/usr/env python
# -*- coding: utf-8 -*-

""" API related with TLV string.

The module provides classes and functions to handle TLV.

__author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
__date__ = "Aug 2015"
__version__ = "0.1.0"

Copyright 2015 XH Smart Card Co,.Ltd

Author: wg@china-xinghan.com
"""

import re, struct, binascii, logging, unittest, collections

#----------------------------------------------------------------------------
a2b = binascii.a2b_hex

def b2a(b):
    return binascii.b2a_hex(b).upper()

#----------------------------------------------------------------------------
class TLVException(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

#----------------------------------------------------------------------------
RE_BERTLV = re.compile(r'([0-9A-F]{2})((?:81)?[0-9A-F]{2})([0-9A-F]*)')

def unpacktlv(tlv):
    ''' 拆分TLV字符串，返回3个元素：t, l, v
        目前仅支持L为0至255的TLV

        tlv: 例如 '61184F10A0000000871002FF86FF0289060100FF50045553494DFFFFFFFFFFFFFFFFFFFFFFFF'
    '''
    t, l, v = '', '', ''

    m = RE_BERTLV.match(tlv)
    if m:
        t, l, v = m.groups()
        if len(l) == 2:
            length = int(l, 16)
            if length<0x80 and ((length+2)*2==len(tlv)):
                return t, l, v
        elif len(l) == 4:
            if l[:2]=='81':
                length = int(l[2:], 16)
                if length>=0x80 and (length+3)*2==len(tlv):
                    return t, l, v
    raise TLVException('%s is not a valid TLV string' % tlv)

def toberlength(length):
    if length <= 0x7F:
        l = '%.2X' % length
    elif length>=0x80 and length<=0xFF :
        l = '81%.2X' % length
    elif length>=0x100 and length<=0xFFFF :
        l = '82%.4X' % length
    else:
        raise TLVException('%d is not a valid TLV length' % length)

    return l

def unpacktlvs(tlvs):
    ''' 将包含多个tlv的字符串拆分为若干个TLV
        
        返回值为若干个3元素的列表
    '''
    tlvs = a2b(tlvs)
    if len(tlvs)<2:
        raise TLVException('%s is not a valid TLVs string' %s (b2a(tlvs)))
    i, m, lst = 0, len(tlvs), []

    while i<m:
        t = tlvs[i+0]
        t = tlvs[i+0:i+2] if (ord(t)&0x1F==0x1F) else t # 'T' needs 2 bytes or 1 bytes
        i += len(t)
        
        l1 = ord(tlvs[i])
        if l1>0x82: #
            raise TLVException('%s is not a valid TLVs string' %s (b2a(tlvs)))
        if l1==0x81:
            length = ord(tlvs[i+1])
            if length<=0x7F:
                raise TLVException('%s is not a valid TLVs string' %s (b2a(tlvs)))
            i += 2
        elif l1==0x82:
            length = struct.unpack('!H', tlvs[i+1:i+3])[0]
            if length<=0x100:
                raise TLVException('%s is not a valid TLVs string' %s (b2a(tlvs)))
            i += 3
        else:
            i += 1
            length = l1

        v = tlvs[i:i+length]
        if len(v)!=length:
            raise TLVException('%s is not a valid TLVs string' %s (b2a(tlvs)))
        i += length

        lst.append([b2a(t), toberlength(len(v)), b2a(v)])
    return lst

def unpacktlvs2dict(tlvs):
    lst = unpacktlvs(tlvs)
    dit = collections.OrderedDict() 
    for x in lst:
        dit[x[0]] = x
    return dit


def jointv(t, v):
    ''' SteppingStones_R7_v100.pdf
        Annex B.5, 'Length Coding'
    '''
    if len(t) < 2:
        raise TLVException("Too short T: %s , %d" % (t, len(t)))
    t, v = a2b(t), a2b(v)
    l = len(v)
    if l >= 0x10000:
        raise TLVException("Too long V: %s , %d" % (v, len(v)))

    if l <= 0x7F:
        tlv = t+chr(l)+v
    elif l>=0x80 and l<=0xFF :
        tlv = t+'\x81'+chr(l)+v
    elif l>=0x100 and l<=0xFFFF :
        tlv = t+'\x82'+ struct.pack('!H', l) +v
    return b2a(tlv)

#-------------------------------------------------------------------------------
class TestModule(unittest.TestCase):
    ''' 模块的单元测试 '''

    def test_jointv(self):
        self.assertEqual(jointv('61','4F10A0000000871002FF86FF0289060100FF50045553494DFFFFFFFFFFFFFFFFFFFFFFFF'), '61244F10A0000000871002FF86FF0289060100FF50045553494DFFFFFFFFFFFFFFFFFFFFFFFF')
        self.assertEqual(jointv('4F','A0000000871002FF86FF0289060100FF'), '4F10A0000000871002FF86FF0289060100FF')
        self.assertEqual(jointv('50','5553494D'), '50045553494D')
        self.assertRaises(TLVException, jointv, '', 'AA')
        self.assertRaises(TLVException, jointv, '1', 'AA')
        self.assertRaises(TLVException, jointv, '01', 'AA'*0x10000)
        self.assertRaises(TLVException, jointv, '01', 'AA'*0x10001)

        for i in range(0x80):
            t = '%.2X' % (i&0xFF)
            self.assertEqual(jointv(t,t*i), t+t+t*i)
        for i in range(0x80, 0x100):
            t = '%.2X' % (i&0xFF)
            self.assertEqual(jointv(t,t*i), t+'81'+t+t*i)
        for i in range(0x100, 0x10000, 0x1000):
            t = '%.2X' % (i&0xFF)
            self.assertEqual(jointv(t,t*i), t+('82%.4X' %i)+t*i)

    def test_toberlength(self):
        for i in range(0x80):
            self.assertEqual('%.2X'%i, toberlength(i))
        for i in range(0x80, 0x100):
            self.assertEqual('81%.2X'%i, toberlength(i))
        for i in range(0x100, 0x10000, 0x1000):
            self.assertEqual('82%.4X'%i, toberlength(i))

    def test_unpacktlv(self):
        for i in range(0x80):
            t = '%.2X' % (i&0xFF)
            tlv = jointv(t,t*i)
            t1, l1, v1 = unpacktlv(tlv)
            self.assertEqual(t, t1)
            self.assertEqual(t, l1)
            self.assertEqual(t*i, v1)
        for i in range(0x80, 0x100):
            t = '%.2X' % (i&0xFF)
            tlv = jointv(t,t*i)
            t1, l1, v1 = unpacktlv(tlv)
            self.assertEqual(t, t1)
            self.assertEqual('81'+t, l1)
            self.assertEqual(t*i, v1)
        self.assertRaises(TLVException, unpacktlv, '')
        self.assertRaises(TLVException, unpacktlv, '1')
        self.assertRaises(TLVException, unpacktlv, 'j')
        self.assertRaises(TLVException, unpacktlv, '1j')
        self.assertRaises(TLVException, unpacktlv, '50005553494D')
        self.assertRaises(TLVException, unpacktlv, '50015553494D')
        self.assertRaises(TLVException, unpacktlv, '50025553494D')
        self.assertRaises(TLVException, unpacktlv, '50035553494D')
        self.assertRaises(TLVException, unpacktlv, '50055553494D')
        self.assertRaises(TLVException, unpacktlv, '50065553494D')
        self.assertRaises(TLVException, unpacktlv, '5081045553494D')
        self.assertRaises(TLVException, unpacktlv, '508200045553494D')
        self.assertRaises(TLVException, unpacktlv, '508270045553494D')

    def test_unpacktlvs(self):
        tlvs = '4F10A0000000871002FF86FF0289060100FF50045553494D'
        tlv1, tlv2 = unpacktlvs(tlvs)
        self.assertEqual('4F10A0000000871002FF86FF0289060100FF', ''.join(tlv1))
        self.assertEqual('50045553494D', ''.join(tlv2))

        # 8202782183023F00A519800171830254C0CB0D00000000000000000000000000CA01008A01058B032F0602C60C90016083010183010A830181
        # 82027821 83023F00 A519800171830254C0CB0D00000000000000000000000000CA0100 8A0105 8B032F0602 C60C90016083010183010A830181
        tlvs = '8202782183023F00A519800171830254C0CB0D00000000000000000000000000CA01008A01058B032F0602C60C90016083010183010A830181'
        lst = unpacktlvs(tlvs)
        self.assertEqual('82027821', ''.join(lst[0]))
        self.assertEqual('83023F00', ''.join(lst[1]))
        self.assertEqual('A519800171830254C0CB0D00000000000000000000000000CA0100', ''.join(lst[2]))
        self.assertEqual('8A0105', ''.join(lst[3]))
        self.assertEqual('8B032F0602', ''.join(lst[4]))
        self.assertEqual('C60C90016083010183010A830181', ''.join(lst[5]))

	
#-------------------------------------------------------------------------------
if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    unittest.main()

