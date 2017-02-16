#!/usr/env python
# -*- coding: utf8 -*-

""" API related with GP.


__author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
__date__ = "Aug 2015"
__version__ = "0.1.0"

Copyright 2015 XH Smart Card Co,.Ltd

Author: atr@china-xinghan.com

Reference Document: 
    1. GlobalPlatform, Card Specification Version 2.1.1, March 2003

"""

#-------------------------------------------------------------------------------
# import utility
import binascii
import logging
import unittest

import api_pcsc
import api_general
import api_alg
import api_cap

from Crypto.Cipher import DES

a2b = api_pcsc.a2b

def b2a(b):
    return api_pcsc.b2a(b).upper()


def LogMessage(msg, level=logging.DEBUG):
    logger = logging.getLogger(__name__)
    logger.log(level, msg)


hexlen = api_general.hexLen
lv = api_general.lv

#-------------------------------------------------------------------------------
# define global variable

CardManagerAID = 'A000000003000000' 
KEY404F = '404142434445464748494A4B4C4D4E4F'

GP_List = [
    'Header',
    'Directory',
    'Import',
    'Applet',
    'Class',
    'Method',
    'StaticField',
    'Export',
    'ConstantPool',
    'RefLocation',
    'Descriptor',
    ]

#-------------------------------------------------------------------------------
# define API

def getBERTLVlengthfield(length):
    ''' ISO/IEC 7816 supports length fields of one, two, ... up to five bytes (see Table 8).
        In ISO/IEC 7816, the values '80' and '85' to 'FF' are invalid for the first byte of length fields. 

        5.2.2.2  BER-TLVlength fields
    '''
    if length<0x7F:
        return '%.2X' % length
    elif length<0x100:
        return '81%.2X' % length
    elif length<0x10000:
        return '82%.4X' % length
    elif length<0x1000000:
        return '83%.6X' % length
    elif length<0x100000000:
        return '84%.8X' % length
    else:
        raise ValueError("Too big a value! %d (%X) can't fit in an ISO/IEC 7816, BER-TLV length field" % (length, length))

def select(aid, expectData='', expectSW='9000', info='', name='GP, Select AID', header='00A40400'):
    ''' Select File (INS : 'A4')
    '''
    return api_pcsc.send(header+lv(aid), expectData=expectData, expectSW=expectSW, info=info, name=name)


def card (aid=CardManagerAID, apduheader='00A40400', expectData='', expectSW='9000', info='', name='GP, /card'):
    ''' Resets the inserted card, requests the ATR and selects the CardManager (default=GlobalPlatform CardManager)
        via the default logical channel (zero).

        Returns a tuple: (response_data, sw1sw2). 
    '''
    api_pcsc.reset()
    ret, sw = select(aid, expectData=expectData, expectSW=expectSW, info=info, name=name, header=apduheader)
    LogMessage('Select Card Manager, Response: %s' % ret)
    return ret, sw


def computerSCP02skey(constant, seq, key, padding='00'*12, icv='00'*8):
    '''
    # DES session keys are created using the static Secure Channel key(s), the Secure Channel Sequence Counter, a 
    # constant, and a padding of binary zeroes. Creating session keys is performed as follows: 

    # E.3.1 Cipher Block Chaining (CBC) 
    # The Initial Chaining Vector (ICV) used for chained data encryption in CBC mode is always 8 bytes of binary zero 
    # ('00'). 

    # E.4.1  DES Session Keys
    # The DES operation used to generate these keys is always triple DES in CBC mode.
    '''
    return api_alg.TDES_Encrypt(constant+seq+padding, key, ecb_mode=False, icv=icv)


def getCMACSkey(s_mac, seq, constant='0101', padding='00'*12, icv='00'*8):
    ''' Secure Channel C-MAC session keys
    '''
    #   Generating the Secure Channel C-MAC session keys using the Secure Channel base key or MAC key 
    # (S-MAC) and the session keys derivation data with a constant of '0101', 
    key = s_mac
    return computerSCP02skey(constant, seq, key, padding, icv)


def getRMACSkey(s_mac, seq, constant='0102', padding='00'*12, icv='00'*8):
    ''' Secure Channel R-MAC session keys
    '''
    #   Generating the Secure Channel R-MAC session keys using the Secure Channel base key or MAC key 
    # (S-MAC) and the session keys derivation data with a constant of '0102', 
    key = s_mac
    return computerSCP02skey(constant, seq, key, padding, icv)


def getEncryptSkey(s_enc, seq, constant='0182', padding='00'*12, icv='00'*8):
    ''' Secure Channel encryption session keys
    '''
    #   Generating the Secure Channel encryption session keys using the Secure Channel base key or encryption 
    # key (S-ENC) and the session keys derivation data with a constant of '0182', 
    key = s_enc
    return computerSCP02skey(constant, seq, key, padding, icv)


def getDataEncryptSkey(dek, seq, constant='0181', padding='00'*12, icv='00'*8):
    ''' Secure Channel data encryption session keys
    '''
    #   Generating the Secure Channel data encryption session keys using the Secure Channel base key or data 
    # encryption key (DEK) and the session keys derivation data with a constant of '0181'. 
    key = dek
    return computerSCP02skey(constant, seq, key, padding, icv)


def iso9797_1_M1_T3(text, key, icv='00'*8):
    """ B.1.2.2  Single DES Plus Final Triple DES MAC 
        This is also known as the Retail MAC. It is as defined in [ISO 9797-1] as MAC Algorithm 1 with output 
        transformation 3, without truncation, and withDES taking the place of the block cipher.

        B.4 DES Padding
        Append an '80' to the right of the data block. 
        If the resultant data block length is a multiple of 8, no further padding is required. 
        Append binary zeroes to the right of the data block until the data block length is a multiple of 8.
    """
    t = a2b(text)
    suffix = '\x80\x00\x00\x00\x00\x00\x00\x00'

    t = t +suffix
    ld = len(t)
    if ld%8:
        padding = ld%8
        t = t[:(-1*padding)]

    k = a2b(key)

    icv = a2b(icv)

    keyA = k[:8]
    keyB = k[8:]

    #desKeyA = pyDes.des(keyA, pyDes.CBC, icv, None)
    #desKeyB = pyDes.des(keyB, pyDes.ECB, None, None)
    #desKeyA1 = pyDes.des(keyA, pyDes.ECB, None, None)

    desKeyA = DES.new(keyA, DES.MODE_CBC, icv)
    desKeyB = DES.new(keyB, DES.MODE_ECB, icv)
    desKeyA1 = DES.new(keyA, DES.MODE_ECB, icv)

    cipher = desKeyA.encrypt(t)
    last8 = cipher[-8:]
    last8d = desKeyB.decrypt(last8)
    mac = desKeyA1.encrypt(last8d)

    return b2a(mac).upper()


def generateCMAC(apdu, skey, icv='00'*8):
    ''' E.4.4  APDU Command C-MAC Generation and Verification

        A C-MAC is generated by an off-card entity and applied across the full APDU command being transmitted to the 
        card including the header and the data field inthe command message. It does not include Le. 

        C-MAC generation and verification uses the Secure Channel C-MAC session key, an ICV and the signature 
        method described in Appendix B.1.2.2 - Single DES Plus Final Triple DES. (Prior to using the ICV, the ICV can 
        be encrypted as described in Appendix E.3.4 - ICV Encryption)

        The signature method, using the Secure Channel C-MAC session key and the ICV, is applied across the padded 
        command message and the resulting 8-byte signature is the C-MAC. The rules for C-MAC padding are as defined 
        in Appendix B.4 - DES Padding. 

    '''
    return iso9797_1_M1_T3(apdu, skey, icv)


def verifyCardCryptogram(host, seq, card, cryptogram, skey, icv='00'*8):
    ''' E.4.2.1  Card Authentication Cryptogram

        Generating or verifying an authentication cryptogram uses the S-ENC session
        key and the signing method described in Appendix B.1.2.1 - Full Triple DES. 

            host: host challenge
            seq: Sequence counter
            card: card challenge
            cryptogram: card cryptogram
            skey: S-ENC session key
            icv: ICV

            Returns True or False
    '''

    # The generation and verification of the card cryptogram is performed by concatenating the 8-byte host challenge, 
    # 2-byte Sequence Counter, and 6-byte card challenge resulting in a 16-byte block. 
    # Applying the same padding rules defined in Appendix B.4 - DES Padding, the data shall be padded with a further 
    # 8-byte block ('80 00 00 00 00 00 00 00').
    padding = '80' +'00'*7
    pt = host + seq + card + padding # 24

    # The signature method, using the S-ENC session key and an ICV of binary zeroes, is applied across this 24-byte 
    # block and the resulting 8-byte signature is the card cryptogram.
    cipher = api_alg.TDES_Encrypt(pt, skey, ecb_mode=False, icv=icv)
    mac = cipher[-16:]

    if mac!=cryptogram:
        LogMessage('Card %s != %s' % (cryptogram, mac))
    #assert mac==cryptogram


def computeHostCryptogram(skey, seq, hostchallenge, cardchallenge, icv='00'*8, padding='80'+'00'*7):
    ''' E.4.2.1  Card Authentication Cryptogram

        Generating or verifying an authentication cryptogram uses the S-ENC session
        key and the signing method described in Appendix B.1.2.1 - Full Triple DES. 

            Returns 'Host Cryptogram' as a string, like 'EF96F8418B0673CE'
    '''

    # The generation and verification of the host cryptogram is performed by concatenating the 2-byte Sequence 
    # Counter, 6-byte card challenge, and 8-byte host challenge resulting in a 16-byte block. 
    # Applying the same padding rules defined in Appendix B.4 - DES Padding, the data shall be padded with a further 
    # 8-byte block ('80 00 00 00 00 00 00 00').
    pt = seq + cardchallenge + hostchallenge + padding # 24

    # The signature method, using the S-ENC session key and an ICV of binary zeroes, is applied across this 24-byte 
    # block and the resulting 8-byte signature is the host cryptogram.
    cipher = api_alg.TDES_Encrypt(pt, skey, ecb_mode=False, icv=icv)
    mac = cipher[-16:]

    return mac


def initupdate (key_version_number='00', host_challenge='', s_enc='', apduheader='8050000008', expectData='', expectSW='9000', info='', name='GP, INITIALIZE-UPDATE'):
    ''' 
        key_version_number: the Key Version Number within the Security Domain to
            be used to initiate the Secure Channel Session. If this value is
            zero, the first available key chosen by the Security Domain will be used.

        Returns a tuple of 2 element: ((kdiv, kver, scpid, seq, cardchallenge, cardcryptogram, hostchallenge), sw).

        Key diversification data  10 bytes 
        Key version number  1 bytes 
        Secure Channel Protocol identifier 1 bytes 
        Sequence Counter  2 bytes 
        Card challenge  6 bytes 
        Card cryptogram  8 bytes
        Host challenge 8 bytes

        See <E.5.1  INITIALIZE UPDATE Command> of [1].
    '''

    if host_challenge:
        r = host_challenge[:]
    else:
        r = api_general.randhex(8)

    apdu = apduheader + r
    response_data, sw = api_pcsc.send(apdu, expectSW=expectSW, info=info, name=name)
    ret = a2b(response_data)
    kdiv, kver, scpid, seq, cardchallenge, cardcryptogram = [b2a(ret[a:b]) for a,b in ((0,10), (10,11), (11,12), (12,14), (14,20), (20,28))]
    if s_enc:
        sk_enc = getEncryptSkey(s_enc, seq)
        verifyCardCryptogram(r, seq, cardchallenge, cardcryptogram, sk_enc)

    t = (kdiv, kver, scpid, seq, cardchallenge, cardcryptogram, r)
    LogMessage('Init-update, (kdiv, kver, scpid, seq, cardchallenge, cardcryptogram, hostchallenge): %s' % str(t).upper())
    return t, sw


def extauth (s_enc, s_mac, seq, cardchallenge, hostchallenge, level='00', expectSW='9000', info='', name='GP, EXTERNAL AUTHENTICATE'):
    ''' 

        See <E.5.2  EXTERNAL AUTHENTICATE Command> of [1].
    '''

    sk_enc = getEncryptSkey(s_enc, seq)
    sk_cmac = getCMACSkey(s_mac, seq)
    hostcryptogram = computeHostCryptogram(sk_enc, seq, hostchallenge, cardchallenge)

    header = '8482%s0010' % level
    pt = header + hostcryptogram
    cmac = generateCMAC(pt, sk_cmac)
    apdu = pt + cmac

    return api_pcsc.send(apdu, expectSW=expectSW, info=info, name=name)


def auth(keyver='00', s_enc=KEY404F, s_mac=KEY404F, level='00'):
    ''' A shortway to do 'init-update' & 'ext-auth' .
    '''
    ret, sw = initupdate(key_version_number=keyver, host_challenge='FF'*8, s_enc=s_enc)
    kdiv, kver, scpid, seq, cardchallenge, cardcryptogram, hostchallenge = ret

    return extauth(s_enc, s_mac, seq, cardchallenge, hostchallenge, level)


def installforload(aid, securitydomainaid=CardManagerAID, datablockhash='', param='', token='', header='80E60200'):
    ''' 9.5.2.3.1  Data Field for INSTALL [for load]

        Mandatory  1  Length of Load File AID 
        Mandatory 5-16  Load File AID 
        Mandatory  1  Length of Security Domain AID 
        Conditional  0-16  Security Domain AID 
        Mandatory  1  Length of Load File Data Block Hash 
        Conditional  0-n  Load File Data Block Hash 
        Mandatory  1  Length of load parameters field 
        Conditional  0-n  Load parameters field 
        Mandatory  1  Length of Load Token 
        Conditional 0-n  Load Token
    '''
    lst = (aid, securitydomainaid, datablockhash, param, token)
    data = ''.join(map(lv, lst))
    apdu = header + lv(data)

    return api_pcsc.send(apdu, expectData='00', expectSW='9000', info='', name='INSTALL for load')


def upload(pathtocap, aid, blocksize=250, clains='80E8'):
    ''' Upload a cap file.
    
        will send INSTALL for load & LOAD Command
    '''
    caps = a2b( api_cap.CAPFile(pathtocap).readAllCap(GP_List) )
    lgth = len(caps)
    c4 = a2b('C4' + getBERTLVlengthfield(lgth)) + caps
    lgth = len(c4)

    blocks = [c4[i:i+blocksize] for i in range(0, lgth, blocksize)]
    assert len(''.join(blocks))==lgth
    assert len(blocks)<=0x100
    apdus = [''.join([clains, '00%.2X'%i, '%.2X'%len(b), b2a(b)]) for i,b in enumerate(blocks)]
    
    lastblock = apdus[-1]
    apdus[-1] = '80E880' +lastblock[6:]

    installforload(aid)

    for apdu in apdus[:-1]:
        api_pcsc.send(apdu, expectData='', expectSW='9000', name='LOAD')
    api_pcsc.send(apdus[-1], expectData='00', expectSW='9000', name='LOAD')


def installforinstall(loadfileaid, moduleaid, appletaid, privileges='00', param='', token='', header='80E60400'):
    ''' 9.5.2.3.2  Data Field for INSTALL [for install]

        Mandatory  1  Length of Executable Load File AID 
        Mandatory  5-16  Executable Load File AID 
        Mandatory  1  Length of Executable Module AID 
        Mandatory 5-16  Executable Module AID 
        Mandatory  1  Length of Application AID 
        Mandatory 5-16  Application AID 
        Mandatory  1  Length of Application Privileges 
        Mandatory 1  Application Privileges 
        Mandatory  1  Length of install parameters field 
        Mandatory 2-n  Install parameters field 
        Mandatory  1  Length of Install Token 
        Conditional  0-n  Install Token
    '''
    lst = (loadfileaid, moduleaid, appletaid, privileges, ('C9'+lv(param)), token)
    data = ''.join(map(lv, lst))
    apdu = header + lv(data)

    return api_pcsc.send(apdu, expectSW='9000', info='', name='INSTALL for install')

def installforinstallselect(loadfileaid, moduleaid, appletaid, privileges='00', param='', token='', header='80E60C00'):
    return installforinstall(loadfileaid, moduleaid, appletaid, privileges, param, token, header)


def install(instanceaid, pkgaid, appletaid='', privileges='00', param=''):
    ''' Short way to install an Applet.

        instanceaid: applet instance aid
        pkgaid: load file aid in GP spec
        appletaid: applet class aid in Java Card spec (module aid in GP spec)

        use instanceaid as moduleaid if appletaid omited
    '''
    if appletaid:
        return installforinstallselect(pkgaid, appletaid, instanceaid, privileges, param)
    else:
        return installforinstallselect(pkgaid, instanceaid, instanceaid, privileges, param)


def deleteaid(aid, related=False, expectSW='9000'):
    ''' The DELETE command is used to delete a uniquely identifiable object such as an Executable Load File, an 
        Application, optionally an Executable Load File and its related Applications.

        Deletion of Key is not yet supported.
    '''
    header = '80E40080' if related else '80E40000'
    data = '4F' + lv(aid)
    apdu = header + lv(data)
    return api_pcsc.send(apdu, expectSW=expectSW, info='', name='Delete AID')


#-------------------------------------------------------------------------------
class TestModule(unittest.TestCase):
    ''' 本模块的单元测试 '''

    def test_helloworld(self):
        ''' 用D:\GPShell-1.4.4\helloworld.cap验证GP相关操作函数的正确性 '''
        r = 'Identiv uTrust 4700 F Contact Reader 0'
        cap = r".\helloworld.cap"
        instance, pkg, applet = 'D0D1D2D3D4D50101', 'D0D1D2D3D4D501', 'D0D1D2D3D4D50101'

        api_pcsc.connectreader(r)
        card()
        auth()
        deleteaid(pkg, True, expectSW='') # omit delete result
        upload(cap, pkg)
        install(instance, pkg, applet)

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    unittest.main()

