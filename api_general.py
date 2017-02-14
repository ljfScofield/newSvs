#!/usr/env python
# -*- coding: utf8 -*-

""" API in common use.


__author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
__date__ = "Aug 2015"
__version__ = "0.1.0"

Copyright 2015 XH Smart Card Co,.Ltd

Author: atr@china-xinghan.com
"""
import random
import binascii
import api_pcsc

#-------------------------------------------------------------------------------
# define utility

def b2a_hex (b):
    a = binascii.b2a_hex(b)
    return a.upper()

a2b_hex = binascii.a2b_hex

b2a = b2a_hex
a2b = a2b_hex


def GetP3Data (data):
    da = data[:0xFF*2]
    p3 = '%.2X' % ((len(da)/2))
    return (p3, da)


def hexLen (s, add=0):
    return '%.2X' % ((len(s)/2)+add)


def lv(s):
    ''' lv('DF00') = '02DF00'
    '''
    return hexLen(s)+s


def randhex (lgth, start=0, stop=0xFF):
    ''' return a random hexdigit string, like '3F00'
    '''
    f = random.randint

    s = ''.join( ['%.2X'%f(start,stop) for x in range(lgth)] )

    return s


def spliteHexStr(hs, lgthlist):
    ''' Splite an hex-digit string to many segments. Example:  spliteHexStr('aaBBBBcc', [1,2,1]) = ['aa', 'BBBB', 'cc']

         hs : 
         lgthlist: a list of lgth, example : [1, 2, 3, 2]

         returns a list of segments if no exception
    '''
    lst = [x*2 for x in lgthlist]

    lst1 = [(sum(lst[:i]), sum(lst[:i])+lst[i]) for i, x in enumerate(lst)]

    return [hs[x:y] for x,y in lst1]


#-------------------------------------------------------------------------------
# define own Exception class

def CreateManyTLV (s, style_list):
    ''' Create many 'TLV' from a string.

            s: hexdigit string in TLV format, like '6F0E8408A000000333CDD000A5028800'
            style: a three elements tuple, indicate the length of 'Tag', 'Len'
    '''
    lst_tlv = []

    for style in style_list:
        tlv, extra = CreateOneTLV(s, style)
        lst_tlv.append( tlv )
        if extra:
            s = extra
            continue
        else:
            break
    
    expect = len(style_list)
    actual = len(lst_tlv)

    if len(lst_tlv)<len(style_list):
        raise api_pcsc.GATException("No enough fields, only %d tlv created. Expect number: %d ." %(actual, expect))
    else:
        if extra:
            raise api_pcsc.GATException("Too many hexdigits! %d more than expect." %(len(extra)/2))

    return lst_tlv


def CreateOneTLV (s, style=(1,1)):
    ''' Create an 'TLV' from string.

            s: hexdigit string in TLV format, like '6F0E8408A000000333CDD000A5028800'
            style: a three elements tuple, indicate the length of 'Tag', 'Len'
    '''

    lgth_Tag = style[0]*2
    lgth_Len = style[1]*2

    try:
        Tag = s[:lgth_Tag]
        Len = s[lgth_Tag:lgth_Tag+lgth_Len]
    except IndexError, ie:
        raise api_pcsc.GATException('Not a valid TLV: %s - %s' % (s, str(ie)))

    if len(Tag)!=lgth_Tag or len(Len)!=lgth_Len:
        raise api_pcsc.GATException('Not a valid TLV: %s - %s' % (s, str(ie)))

    x = int(Len, 16)*2
    Value = s[lgth_Tag+lgth_Len:lgth_Tag+lgth_Len+x]

    if len(Value) != x:
        raise api_pcsc.GATException("Not a valid TLV: %s - no enough fields for the 'Value' part" % s)
    else:
        extra = s[lgth_Tag+lgth_Len+x:]


    tlv = (Tag, Len, Value)

    return (tlv, extra)



#-------------------------------------------------------------------------------
# define API

def SelectFile (cla='00', p1='04', p2='00', data='', expectSW='9000', info='', name='Select File'):
    ''' Select File (INS : 'A4')

            cla:
            p1:
            p2:
            data: data to be sent to card, default is empty. 'P3' will be caculated automatic.
            expectSW: 
            name: only for display

        Returns a two elements tuple: (response-data, sw1sw2)

        See <ISO 7816-4> 7.1.1
    '''

    p3, da = GetP3Data(data)

    response_data = api_pcsc.SendAPDU(cla=cla, ins='A4', p1=p1, p2=p2, p3=p3, data=da, expectSW=expectSW, info=info, name=name)

    sw = api_pcsc.GetSW()

    return (response_data, sw)


def GetChallenge (cla='00', p1='00', p2='00', p3='04', expectData='', expectSW='9000', info='', name='Get Challenge'):
    ''' Get Challenge (INS : '84')

            cla:
            p1:
            p2:
            p3: 
            expectSW: 
            name: only for display

        Returns a two elements tuple: (response-data, sw1sw2)

        See <ISO 7816-4> 7.5.3
    '''

    response_data = api_pcsc.SendAPDU(cla=cla, ins='84', p1=p1, p2=p2, p3=p3, data='',
            expectData=expectData, expectSW=expectSW, info=info, name=name)

    sw = api_pcsc.GetSW()

    return (response_data, sw)


def GetData (cla, p1, p2, p3='02', expectData='', expectSW='9000', info='', name='Get Data'):
    ''' Get Data (INS : 'CA')

            cla:
            p1:
            p2:
            p3: 
            expectSW: 
            name: only for display

        Returns a two elements tuple: (response-data, sw1sw2)

        See <ISO 7816-4> 7.4.2
    '''

    response_data = api_pcsc.SendAPDU(cla=cla, ins='CA', p1=p1, p2=p2, p3=p3, data='',
            expectData=expectData, expectSW=expectSW, info=info, name=name)

    sw = api_pcsc.GetSW()

    return (response_data, sw)


def InternalAuth (data, cla='00', p1='00', p2='00', p3='08', expectSW='9000', info='', name='Internal Authenticate'):
    ''' Internal Authenticate (INS : '88')

            data:
            cla:
            p1:
            p2:
            p3: 
            expectSW: 
            name: only for display

        Returns a two elements tuple: (response-data, sw1sw2)

        See <ISO 7816-4> 7.5.2
    '''

    response_data = api_pcsc.SendAPDU(cla=cla, ins='88', p1=p1, p2=p2, p3=p3, data=data, expectSW=expectSW, info=info, name=name)

    sw = api_pcsc.GetSW()

    return (response_data, sw)


def ExternalAuth (data, cla='00', p1='00', p2='00', p3='08', expectSW='9000', info='', name='External Authenticate'):
    ''' External Authenticate (INS : '82')

            data:
            cla:
            p1:
            p2:
            p3: 
            expectSW: 
            name: only for display

        Returns a two elements tuple: (response-data, sw1sw2)

        See <ISO 7816-4> 7.5.4
    '''

    response_data = api_pcsc.SendAPDU(cla=cla, ins='82', p1=p1, p2=p2, p3=p3, data=data, expectSW=expectSW, info=info, name=name)

    sw = api_pcsc.GetSW()

    return (response_data, sw)


def sfi2p2_B2 (sfi):
    ''' build 'P2' base on sfi

        sfi: string, like '0F'
    '''

    p2 = '%.2X' % (((int(sfi,16)<<3)+0x04)&0xFF)

    return p2

def ReadRecordExt (sfi, recno, p3, expectData='', expectSW='9000', info='', name='Read Record'):
    ''' Read Binary (INS : 'B2')

            cla:
            p1:
            p2:
            p3: 
            expectSW: 
            name: only for display

        Returns a two elements tuple: (response-data, sw1sw2)

        See <ISO 7816-4> 7.3.3
    '''

    response_data = api_pcsc.SendAPDU(cla='00', ins='B2', p1=recno, p2=sfi2p2_B2(sfi), p3=p3, data='',
            expectData=expectData, expectSW=expectSW, info=info, name=name)

    sw = api_pcsc.GetSW()

    return (response_data, sw)


def ReadRecord (cla, p1, p2, p3, expectData='', expectSW='9000', info='', name='Read Record'):
    ''' Read Binary (INS : 'B2')

            cla:
            p1:
            p2:
            p3: 
            expectSW: 
            name: only for display

        Returns a two elements tuple: (response-data, sw1sw2)

        See <ISO 7816-4> 7.3.3
    '''

    response_data = api_pcsc.SendAPDU(cla=cla, ins='B2', p1=p1, p2=p2, p3=p3, data='',
            expectData=expectData, expectSW=expectSW, info=info, name=name)

    sw = api_pcsc.GetSW()

    return (response_data, sw)


def ReadBinary (cla, p1, p2, p3, expectData='', expectSW='9000', info='', name='Read Binary'):
    ''' Read Binary (INS : 'B0')

            cla:
            p1:
            p2:
            p3: 
            expectSW: 
            name: only for display

        Returns a two elements tuple: (response-data, sw1sw2)

        See <ISO 7816-4> 7.2.3
    '''

    response_data = api_pcsc.SendAPDU(cla=cla, ins='B0', p1=p1, p2=p2, p3=p3, data='',
            expectData=expectData, expectSW=expectSW, info=info, name=name)

    sw = api_pcsc.GetSW()

    return (response_data, sw)


def UpdateBinary (cla, p1, p2, p3, data='', expectSW='9000', info='', name='Update Binary'):
    ''' Update Binary (INS : 'D6')

            cla:
            p1:
            p2:
            p3: 
            data:
            expectSW: 
            info: 
            name: only for display

        Returns a two elements tuple: (response-data, sw1sw2)

        See <ISO 7816-4> 7.2.4
    '''

    response_data = api_pcsc.SendAPDU(cla=cla, ins='D6', p1=p1, p2=p2, p3=p3, data=data,
            expectSW=expectSW, info=info, name=name)

    sw = api_pcsc.GetSW()

    return (response_data, sw)


def VerifyPIN (cla, p1, p2, p3, data='', expectSW='9000', info='', name='Verify PIN'):
    ''' Verify PIN (INS : '20')

            cla:
            p1:
            p2:
            p3: 
            data:
            expectSW: 
            info: 
            name: only for display

        Returns a two elements tuple: (response-data, sw1sw2)

        See <ISO 7816-4> 7.5.6
    '''

    response_data = api_pcsc.SendAPDU(cla=cla, ins='20', p1=p1, p2=p2, p3=p3, data=data,
            expectSW=expectSW, info=info, name=name)

    sw = api_pcsc.GetSW()

    return (response_data, sw)


def GetResponse (cla, p1, p2, p3, expectData='', expectSW='9000', info='', name='Get Response'):
    ''' Get Response (INS : 'C0')

            cla:
            p1:
            p2:
            p3: 
            expectSW: 
            name: only for display

        Returns a two elements tuple: (response-data, sw1sw2)

        See <ISO 7816-4> 7.6.1
    '''

    response_data = api_pcsc.SendAPDU(cla=cla, ins='C0', p1=p1, p2=p2, p3=p3, data='',
            expectData=expectData, expectSW=expectSW, info=info, name=name)

    sw = api_pcsc.GetSW()

    return (response_data, sw)


#-------------------------------------------------------------------------------
if __name__ == '__main__':
    pass

