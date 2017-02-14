#!/usr/env python
# -*- coding: utf8 -*-

""" MAC tool v1.0.0 2010-0604 """

import binascii
import pyDes
import string
import ctypes
import random

MODE_SHIFT_Right = 1
MODE_SHIFT_Left = 0

a2b_hex = binascii.a2b_hex
b2a_hex = binascii.b2a_hex


def Bits2Ascii(bits):
    ''' '''
    dt = {
    '0000':'0',
    '0001':'1',
    '0010':'2',
    '0011':'3',
    '0100':'4',
    '0101':'5',
    '0110':'6',
    '0111':'7',
    '1000':'8',
    '1001':'9',
    '1010':'A',
    '1011':'B',
    '1100':'C',
    '1101':'D',
    '1110':'E',
    '1111':'F',
            }

    asc = ''.join( [dt[bits[x:x+4]] for x in range(0, len(bits), 4)] )

    return asc

def Ascii2Bits(asc):
    dt = {
    '0':'0000',
    '1':'0001',
    '2':'0010',
    '3':'0011',
    '4':'0100',
    '5':'0101',
    '6':'0110',
    '7':'0111',
    '8':'1000',
    '9':'1001',
    'A':'1010',
    'B':'1011',
    'C':'1100',
    'D':'1101',
    'E':'1110',
    'F':'1111',
    }

    bits = ''.join([dt[x] for x in asc.upper()])

    return bits

def ShiftBits(asc, bits, mode, pad='0'):
    # '468ACF00' == ShiftBits('12345678', 5, MODE_SHIFT_Left)
    # '0091A2B3' == ShiftBits('12345678', 5, MODE_SHIFT_Right)

    if bits <= 0 or bits >= 8:
        return

    if mode != MODE_SHIFT_Right and mode != MODE_SHIFT_Left:
        return

    if pad != '0' and pad != '1':
        return

    ascBits = Ascii2Bits(asc)

    if mode == MODE_SHIFT_Right:
        ascBits = (bits*pad) + ascBits +(8-bits)*pad
    else:
        ascBits = ascBits[bits:] + (bits*pad)

    newasc =  Bits2Ascii(ascBits)
    return newasc


def XorStr(s1, s2):
    s1 = s1.upper()
    s2 = s2.upper()

    bin1 = a2b_hex(s1)
    bin2 = a2b_hex(s2)

    out = ''
    for i,x in enumerate(bin1):
        y1 = (ctypes.c_ubyte(~ord(x)).value) &0xFF
        y2 = (ctypes.c_ubyte(~ord(bin2[i])).value) &0xFF
        y = chr( y1^y2 )
        out += y

    text = b2a_hex(out)

    return text.upper()

def NotStr(s):
    bin = a2b_hex(s)
    s1 = ''
    for x in bin:
        y = chr((ctypes.c_ubyte(~ord(x)).value) &0xFF)
        s1 += y

    text = b2a_hex(s1)
    return text.upper()


def DES_MAC_Precheck(icv, datain, key):
    ''' prepare check for DES MAC generation

        Returns a tuple consists 3 elements:  flag, title, message
    '''

    title = 'DES MAC Precheck'

    lst = [icv, datain, key]

    for x in lst:
        try:
            b = a2b_hex(x)
        except TypeError, e:
            return False, title, x[:16]+"\n"+str(e)

    lgth = len(icv)
    if lgth != 16:
        return False, title, 'Invalid ICV: should be 16 hexdigits, not %d.' % lgth

    # no need to check 'datain' length when generating MAC

    # key
    lgth = len(key)

    if lgth != 16:
        return False, title, 'Invalid Key: should be 16 hexdigits, not %d.' % lgth

    return True, title, 'OK'


def TDES_MAC_Precheck(icv, datain, key):
    ''' prepare check for TDES MAC generation 

        Returns a tuple consists 3 elements:  flag, title, message
    '''

    title = 'TDES Precheck'

    lst = [icv, datain, key]

    for x in lst:
        try:
            b = a2b_hex(x)
        except TypeError, e:
            return False, title, x[:16]+"\n"+str(e)

    lgth = len(icv)
    if lgth != 16:
        return False, title, 'Invalid ICV: should be 16 hexdigits, not %d.' % lgth


    # no need to check length of 'datain' when generating MAC


    # key
    lgth = len(key)

    if lgth not in [32, 48]:
        return False, title, 'Invalid Key: should be 32 or 48 hexdigits, not %d.' % lgth

    return True, title, 'OK'

def DES_Precheck(icv, datain, key, ecb_mode):
    ''' prepare check for DES crypto

        Returns a tuple consists 3 elements:  flag, title, message
    '''

    title = 'DES Precheck'

    if ecb_mode:
        lst = [datain, key] # icv skipped
    else:
        lst = [icv, datain, key]

    for x in lst:
        try:
            b = a2b_hex(x)
        except TypeError, e:
            return False, title, x[:16]+"\n"+str(e)

    if not ecb_mode:
        lgth = len(icv)
        if lgth != 16:
            return False, title, 'Invalid ICV: should be 16 hexdigits, not %d.' % lgth

    lgth = len(datain)

    if lgth < 16:
        return False, title, 'Invalid data: should be 16*N hexdigits, not %d.' % lgth

    if lgth%16:
        return False, title, 'Invalid data: should be 16*N hexdigits, %d %% 16 == %d.' % (lgth, lgth%16)

    lgth = len(key)

    if lgth != 16:
        return False, title, 'Invalid Key: should be 16 hexdigits, not %d.' % lgth

    return True, title, 'OK'


def TDES_Precheck(icv, datain, key, ecb_mode):
    ''' prepare check for TDES crypto

        Returns a tuple consists 3 elements:  flag, title, message
    '''

    title = 'TDES Precheck'

    if ecb_mode:
        lst = [datain, key] # icv skipped
    else:
        lst = [icv, datain, key]

    for x in lst:
        try:
            b = a2b_hex(x)
        except TypeError, e:
            return False, title, x[:16]+"\n"+str(e)

    if not ecb_mode:
        lgth = len(icv)
        if lgth != 16:
            return False, title, 'Invalid ICV: should be 16 hexdigits, not %d.' % lgth

    lgth = len(datain)

    if lgth < 16:
        return False, title, 'Invalid data: should be 16*N hexdigits, not %d.' % lgth

    if lgth%16:
        return False, title, 'Invalid data: should be 16*N hexdigits, %d %% 16 == %d.' % (lgth, lgth%16)

    lgth = len(key)

    if lgth not in [32, 48]:
        return False, title, 'Invalid Key: should be 32 or 48 hexdigits, not %d.' % lgth

    return True, title, 'OK'


def DES_Encrypt(datain, key, ecb_mode, icv=None):
    ''' DES Encrypt function

        datain: string, like '1122334455667788'
        key:    string, like '5566778811223344'
        ecb_mode: True/False
        icv:    string, like '5566778811223344'
    '''

    d = a2b_hex(datain)
    k = a2b_hex(key)

    if ecb_mode:
        cpu = pyDes.des(k, pyDes.ECB)
        dataout = cpu.encrypt(d)
    else:
        i = a2b_hex(icv)
        cpu = pyDes.des(k, pyDes.CBC, i)
        dataout = cpu.encrypt(d)

    return b2a_hex(dataout).upper()


def DES_Decrypt(datain, key, ecb_mode, icv=None):
    ''' DES Decrypt function

        datain: string, like '1122334455667788' MUST BE 16*N
        key:    string, like '5566778811223344' MUST BE 16
        ecb_mode: True/False
        icv:    string, like '5566778811223344' MUST BE 16
    '''

    d = a2b_hex(datain)
    k = a2b_hex(key)

    if ecb_mode:
        cpu = pyDes.des(k, pyDes.ECB)
        dataout = cpu.decrypt(d)
    else:
        i = a2b_hex(icv)
        cpu = pyDes.des(k, pyDes.CBC, i)
        dataout = cpu.decrypt(d)

    return b2a_hex(dataout).upper()


def TDES_Encrypt(datain, key, ecb_mode=True, icv=None):
    ''' TDES Encrypt function

        datain: string, like '1122334455667788' MUST BE 16*N
        key:    string, like '55667788112233445566778811223344' MUST BE 32 or 48
        ecb_mode: True/False
        icv:    string, like '5566778811223344' MUST BE 16
    '''

    d = a2b_hex(datain)
    k = a2b_hex(key)

    if ecb_mode:
        cpu = pyDes.triple_des(k, pyDes.ECB)
        dataout = cpu.encrypt(d)
    else:
        i = a2b_hex(icv)
        cpu = pyDes.triple_des(k, pyDes.CBC, i)
        dataout = cpu.encrypt(d)

    return b2a_hex(dataout).upper()


def TDES_Decrypt(datain, key, ecb_mode=True, icv=None):
    ''' TDES Decrypt function

        datain: string, like '1122334455667788' MUST be 16*N
        key:    string, like '55667788112233445566778811223344' MUST be 32 or 48
        ecb_mode: True/False
        icv:    string, like '5566778811223344' MUST BE 16
    '''

    d = a2b_hex(datain)
    k = a2b_hex(key)

    if ecb_mode:
        cpu = pyDes.triple_des(k, pyDes.ECB)
        dataout = cpu.decrypt(d)
    else:
        i = a2b_hex(icv)
        cpu = pyDes.triple_des(k, pyDes.CBC, i)
        dataout = cpu.decrypt(d)

    return b2a_hex(dataout).upper()


def PBOC_TDES_MAC32(text, key, iv='00'*8):

    t = a2b_hex(text)
    suffix = '\x80\x00\x00\x00\x00\x00\x00\x00'

    t = t +suffix
    ld = len(t)
    if ld%8:
        padding = ld%8
        t = t[:(-1*padding)]

    k = a2b_hex(key)

    iv = a2b_hex(iv)

    keyA = k[:8]
    keyB = k[8:]

    desKeyA = pyDes.des(keyA, pyDes.CBC, iv, None)
    desKeyB = pyDes.des(keyB, pyDes.ECB, None, None)
    desKeyA1 = pyDes.des(keyA, pyDes.ECB, None, None)

    cipher = desKeyA.encrypt(t)
    last8 = cipher[-8:]
    last8d = desKeyB.decrypt(last8)
    last8de = desKeyA1.encrypt(last8d)

    mac = last8de[:4]

    return b2a_hex(mac).upper()


def PBOC_SDES_MAC32(text, key, iv='00'*8):

    t = a2b_hex(text)
    suffix = '\x80\x00\x00\x00\x00\x00\x00\x00'

    t = t +suffix
    ld = len(t)
    if ld%8:
        padding = ld%8
        t = t[:(-1*padding)]

    k = a2b_hex(key)

    iv = a2b_hex(iv)

    desKeyA = pyDes.des(k, pyDes.CBC, iv, None)
    
    cipher = desKeyA.encrypt(t)
    last8 = cipher[-8:]

    mac = last8[:4]

    return b2a_hex(mac).upper()


def PBOC_TDES_Encrypt(plaintext, key):

    key = key[:0x20]
    plaintext = plaintext[:0xFF*2]

    k = a2b_hex(key.upper())
    pt = a2b_hex(plaintext.upper())

    ld = len(pt)

    pt = chr(ld) +pt

    if len(pt)%8 != 0:
        pt = pt +"\x80\x00\x00\x00\x00\x00\x00\x00"
        l = len(pt) -(len(pt)%8)
        pt = pt[:l]


    fun = pyDes.triple_des(k, pyDes.ECB, None, None)

    cipher = fun.encrypt(pt)

    return b2a_hex(cipher).upper()


def SDES_MAC_Right(text, key, iv='00'*0x08):
    """
        SDES MAC: DES-CBC, return the right-side 4 byte of the result
    """

    iv = a2b_hex(iv)

    text = a2b_hex(text)

    suffix = '\x80\x00\x00\x00\x00\x00\x00\x00'
    newtext = text+suffix
    l = len(newtext)
    l = l - (l%8)
    newtext = newtext[:l]


    key = a2b_hex(key)

    descpu = pyDes.des(key, pyDes.CBC, iv, None)

    cipher = descpu.encrypt(newtext)

    l = len(cipher)
    last8e = cipher[l-8:]

    mac = last8e[:4]

    ciphertext = ""
    for x in mac:
        ciphertext += "%.2X"%ord(x)

    return ciphertext


def SDES_MAC_Left(text, key, iv='00'*0x08):
    """SDES MAC """

    iv = a2b_hex(iv)

    text = a2b_hex(text)

    suffix = '\x80\x00\x00\x00\x00\x00\x00\x00'
    newtext = text+suffix
    l = len(newtext)
    l = l - (l%8)
    newtext = newtext[:l]


    key = a2b_hex(key)

    descpu = pyDes.des(key, pyDes.CBC, iv, None)

    cipher = descpu.encrypt(newtext)

    l = len(cipher)
    last8e = cipher[l-8:]

    mac = last8e[:8]

    ciphertext = ""
    for x in mac:
        ciphertext += "%.2X"%ord(x)

    return ciphertext[:8]


def SDES_MAC(text, key, iv='00'*0x08):
    """SDES MAC """

    iv = a2b_hex(iv)

    text = a2b_hex(text)

    suffix = '\x80\x00\x00\x00\x00\x00\x00\x00'
    newtext = text+suffix
    l = len(newtext)
    l = l - (l%8)
    newtext = newtext[:l]


    key = a2b_hex(key)

    descpu = pyDes.des(key, pyDes.CBC, iv, None)

    cipher = descpu.encrypt(newtext)

    l = len(cipher)
    last8e = cipher[l-8:]

    mac = last8e[:8]

    ciphertext = ""
    for x in mac:
        ciphertext += "%.2X"%ord(x)

    return ciphertext


def TDES_MAC_Right(text, key, iv='00'*8):
    iv = a2b_hex(iv)

    text = a2b_hex(text)
    suffix = '\x80\x00\x00\x00\x00\x00\x00\x00'
    newtext = text+suffix
    l = len(newtext)
    l = l - (l%8)
    newtext = newtext[:l]

    key = a2b_hex(key)

    keyL = key[:8]

    keyR = key[8:]

    descpu = pyDes.des(keyL, pyDes.CBC, iv, None)

    cipher = descpu.encrypt(newtext)

    l = len(cipher)
    last8e = cipher[l-8:]

    descpu1 = pyDes.des(keyR, pyDes.ECB, None, None)
    last8ed = descpu1.decrypt(last8e)

    descpu2 = pyDes.des(keyL, pyDes.ECB, None, None)
    last8ede = descpu2.encrypt(last8ed)

    mac = last8ede[:4]

    #ciphertext = "".join(map("%.2X"%ord(x), mac))
    ciphertext = ""
    for x in mac:
        ciphertext += "%.2X"%ord(x)

    return ciphertext 


def TDES_MAC(text, key, iv='00'*8):
    iv = a2b_hex(iv)

    text = a2b_hex(text)
    suffix = '\x80\x00\x00\x00\x00\x00\x00\x00'
    newtext = text+suffix
    l = len(newtext)
    l = l - (l%8)
    newtext = newtext[:l]

    key = a2b_hex(key)

    if len(key) == 16: # TDES with 2 keys
        keyL = key[:8]
        keyM = None
        keyR = key[8:]
    else: # 24, TDES with 3 keys
        keyL = key[0:8]
        keyM = key[8:16]
        keyR = key[16:]

    descpu = pyDes.des(keyL, pyDes.CBC, iv, None)

    cipher = descpu.encrypt(newtext)

    l = len(cipher)
    last8e = cipher[l-8:]

    if keyM: # TDES with 3 keys
        descpu1 = pyDes.des(keyM, pyDes.ECB, None, None)
        last8ed = descpu1.decrypt(last8e)

        descpu2 = pyDes.des(keyR, pyDes.ECB, None, None)
        last8ede = descpu2.encrypt(last8ed)
    else:
        descpu1 = pyDes.des(keyR, pyDes.ECB, None, None)
        last8ed = descpu1.decrypt(last8e)

        descpu2 = pyDes.des(keyL, pyDes.ECB, None, None)
        last8ede = descpu2.encrypt(last8ed)

    mac = last8ede

    #ciphertext = "".join(map("%.2X"%ord(x), mac))
    ciphertext = ""
    for x in mac:
        ciphertext += "%.2X"%ord(x)

    return ciphertext # 


def TDES_MAC_Unusual(text, key, iv='00'*8):
    iv = a2b_hex(iv)

    text = a2b_hex(text)
    suffix = '\x80\x00\x00\x00\x00\x00\x00\x00'
    newtext = text+suffix
    l = len(newtext)
    l = l - (l%8)
    newtext = newtext[:l]

    key = a2b_hex(key)

    keyL = key[:8]

    keyR = key[8:]

    descpu = pyDes.des(keyL, pyDes.CBC, iv, None)

    cipher = descpu.encrypt(newtext)

    l = len(cipher)
    last8e = cipher[l-8:]

    tdescpu = pyDes.triple_des(key, pyDes.ECB, None, None)
    last8et = tdescpu.encrypt(last8e)

    mac = last8et

    #ciphertext = "".join(map("%.2X"%ord(x), mac))
    ciphertext = ""
    for x in mac:
        ciphertext += "%.2X"%ord(x)

    return ciphertext # 


def Get3DESLevel1SubKey(key, factor1):

    # factor1

    if len(factor1) != 16:
        return factor1 +" : " +str(len(factor1)) +" : [Error] Should be 16"

    if len(key) != 32:
        return str(x)+" : " +str(len(x)) +" : [Error] Should be 32"

    f1 = a2b_hex(factor1)
    f1Xor = ''.join( map(lambda x:chr(0xFF^ord(x)), f1) )

    keyhex = a2b_hex(key)

    cpu = pyDes.triple_des(keyhex, pyDes.ECB, None, None)

    subkey1 = cpu.encrypt(f1)+cpu.encrypt(f1Xor)

    subkey1text = ''.join( map(lambda x:"%.2X"%ord(x), subkey1) )

    return subkey1text


def Get3DESLevel2SubKey(key, factor1, factor2):

    # factor1
    # factor2 

    if len(factor1) != 16 or len(factor2) != 16:
        return str(len(factor1)) +" : [Error] Should be 16"

    # key

    if len(key) != 32:
        return str(x)+" : " +str(len(x)) +" : [Error] Should be 32"

    factor1 = a2b_hex(factor1)
    factor1Xor = ""
    for x in factor1:
        factor1Xor += (chr(0xFF^ord(x)))

    factor2 = a2b_hex(factor2)
    factor2Xor = ""
    for x in factor2:
        factor2Xor += (chr(0xFF^ord(x)))

    keyhex = a2b_hex(key)

    cpu = pyDes.triple_des(keyhex, pyDes.ECB, None, None)

    subkey1 = cpu.encrypt(factor1) + cpu.encrypt(factor1Xor)

    cpu = pyDes.triple_des(subkey1, pyDes.ECB, None, None)

    subkey2 = cpu.encrypt(factor2) + cpu.encrypt(factor2Xor)

    subkey2text = ""
    for x in subkey2:
        subkey2text += "%.2X"%ord(x)


    return subkey2text

def zyt_create_file(key, fileheader, rand='', apduheader='84E00001'):

    pt = fileheader

    if apduheader[:2]=='84':
        pt = apduheader +'%.2X'%((len(pt)/2)+4) + pt # apdu header +Lc + header
        mac = PBOC_TDES_MAC32(pt, key, rand+'00'*4) 
        apdu = pt + mac
    else:
        pt = apduheader +'%.2X'%(len(pt)/2) + pt
        apdu = pt

    return apdu

def zyt_write_key(key, newkey, rand, apduheader='84D40000'):

    pt = newkey # 

    cipher = ZYT_TDES_Encrypt(pt, key) # 

    pt = apduheader +'%.2X'%((len(cipher)/2)+4) + cipher 

    mac = PBOC_TDES_MAC32(pt, key, rand+'00'*4) # 

    apdu = pt + mac

    return apdu



if __name__ == '__main__':
    lst = '0123456789ABCDEF'
    lstbit = Ascii2Bits(lst)
    lstbitlst = Bits2Ascii(lstbit)

    if cmp(lst.upper(), lstbitlst.upper()) != 0:
        print "error in Ascii2Bits() Bits2Ascii()"

    s = '468ACF00'
    s1 = ShiftBits('12345678', 5, MODE_SHIFT_Left)
    s2 = '0091A2B3C0'
    s3 = ShiftBits('12345678', 5, MODE_SHIFT_Right)
    if cmp(s.upper(), s1.upper()) != 0 or cmp(s2.upper(), s3.upper()) != 0:
        print "error in ShiftBits()"

    lst = '62'
    lstReverse = NotStr(lst)
    lstReverseReverse = NotStr(lstReverse)

    if cmp(lst.upper(), lstReverseReverse.upper()) != 0:
        print 'error in NotStr()'

    text = '514602B602261D20'
    key = '514602B602261D21514602B602261D21'
    iv = '514602B602261D22'
    mac = '10D82B28'
    mac1 = PBOC_TDES_MAC32(text, key, iv)

    if cmp(mac.upper(), mac1.upper()) != 0:
        print 'error in PBOC_TDES_MAC32()'


    pt = ''
    k = '74832174819274982147298749475847'
    ct = '5504224C647CF703'
    ct1 = PBOC_TDES_Encrypt(pt, k)

    if cmp(ct.upper(), ct1.upper()) != 0:
        print 'error in PBOC_TDES_Encrypt()'


    pt = '74832174819274982147298749234721348132658712658712568172365872165817'
    k = '74832174819274982147298749475847'
    ct = 'C2456064D2FEA807BD492230ECC386DF36D7775922E74EE29D7810BDEF453743C88B07721CF541BC'
    ct1 = PBOC_TDES_Encrypt(pt, k)

    if cmp(ct.upper(), ct1.upper()) != 0:
        print 'error in PBOC_TDES_Encrypt()'

    pt = '00'*0xFF
    k = '74832174819274982147298749475847'
    ct = '0294C00364B6037AA34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03A34F395B54DB7C03'
    ct1 = PBOC_TDES_Encrypt(pt, k)

    if cmp(ct.upper(), ct1.upper()) != 0:
        print len(pt)
        print len(ct)
        print len(ct1)
        print 'error in PBOC_TDES_Encrypt()'

    k = '74832174819274982147298749475847'
    f = '7483217481927498'
    dlk = '0F591D96D2A1BB4499D8A17DAFE0C637'
    dlk1 = Get3DESLevel1SubKey(k, f)
    if cmp(dlk.upper(), dlk1.upper()) != 0:
        print 'error in Get3DESLevel1SubKey()'

    k = '7483217481927498'
    t = '0F591D96D2A1BB4499D8A17DAFE0C637'
    mac = '2BC78D18'
    mac1 = SDES_MAC_Right(t, k)
    if cmp(mac.upper(), mac1.upper()) != 0:
        print 'error in SDES_MAC_Right()'

    k = '7483217481927498'
    t = '0F591D96D2A1BB4499D8A17DAFE0C637'
    iv = '7483217481927498'
    mac = '423BC334'
    mac1 = SDES_MAC_Right(t, k, iv)
    if cmp(mac.upper(), mac1.upper()) != 0:
        print 'error in SDES_MAC_Right()'

    k = '94832174819274987483217481927499'
    t = '0F591D96D2A1BB4499D8A17DAFE0C637'
    iv = '0000000000000000'
    mac = '6D6979E6'
    mac1 = TDES_MAC_Right(t, k, iv)
    if cmp(mac.upper(), mac1.upper()) != 0:
        print 'error in TDES_MAC_Right()'

    iv = '6D6979E600000000'
    mac = '505D95DA'
    mac1 = TDES_MAC_Right(t, k, iv)
    if cmp(mac.upper(), mac1.upper()) != 0:
        print 'error in TDES_MAC_Right()'

    k = '11111111111111111111111111111111'
    f1 = '1111111111111111'
    f2 = '2111111111111111'
    subkey = 'C3697E7CE603FA11A391196CA7B7F967'
    subkey1 = Get3DESLevel2SubKey(k, f1, f2)
    if cmp(subkey1.upper(), subkey.upper()) != 0:
        print subkey
        print subkey1
        print 'error in Get3DESLevel2SubKey()'

    s1 = '5DEDC06EA93F7579'
    s2 = '3B6676248EBFB9A9'
    s = XorStr(s1, s2)
    if s != '668BB64A2780CCD0':
        print s1
        print s2
        print s
        print 'error in XorStr()'

    print 'KeyAlgMac self test finished!'

