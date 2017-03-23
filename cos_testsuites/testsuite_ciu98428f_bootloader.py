#!/usr/env python
# -*- coding: utf-8 -*-

""" 通过CIU98428F自带的bootloader，对其样卡的FLASH做压力测试

__author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
__date__ = "Jan 2016"
__version__ = "0.1.0"

Copyright 2017 XH Smart Card Co,. Ltd

Author: wg@china-xinghan.com
"""

import logging, os, webbrowser, unittest, random

from Crypto.Cipher import DES

import api_pcsc
import api_util
import api_unittest

import api_crc

#----------------------------------------------------------------------------
u = api_util.u

a2b = api_pcsc.a2b

def b2a(b):
    return api_pcsc.b2a(b).upper()

ATR = '3B1D968118031000003E06010000C300'
#ATR ='3B1D968118031000003E 06010000 C3 00'

STATUS = {
        '00' : u'下载态',
        '54' : u'混态（固件数据区自检错误）',
        '53' : u'Loader代码自检错误',
        }

PIN = 'FF' * 8
KEY = 'FF' * 16
PAGESIZE = 0x200

#----------------------------------------------------------------------------
class Bootloader(object):
    ''' CIU98428F_芯片Loader用户使用手册.pdf '''


    def verifypin(self, pin=PIN, expectSW='9000'):
        return api_pcsc.send('BF20000108'+pin, expectSW=expectSW, info='Verify PIN')

    def changepin(self, old, new):
        return api_pcsc.send('BF24000010'+old+new, info='Change PIN')

    def changekey(self, old, new):
        des = DES.new(a2b(old), DES.MODE_ECB, None)
        cipher = des.encrypt(a2b(new+'80'+'00'*7))
        return api_pcsc.send('BF24010010'+b2a(cipher), info='Change Key, new key ' + new)

    def erasepage(self, start, end, erasevector=False):
        if not erasevector:
            if start==0:
                raise ValueError(u'请注意！请谨慎擦除CIU98428F的首页')
        return api_pcsc.send('BFEE00FF04%.4X%.4X' % (start&0xFFFF, end &0xFFFF), info='Erase Page')

    def plaindownload(self, start, data):
        lgth = len(data)
        if lgth > 256*2:
            raise ValueError(u'写入数据太长 %d/2，一条APDU最多允许256字节' % lgth)
        else:
            apdu = 'B'+data[-2] + '7'+data[-1] + '%.4X'%(start&0xFFFF) + '%.2X'%(lgth/2-1) + data[:-2]
            return api_pcsc.send(apdu, info='Plain Download, %d bytes' % (lgth/2))

    def cipherdownload(self, start, data, key=KEY):
        lgth = len(data)
        lgth1 = (lgth/2 +7) % 8 # 填充后长度
        if lgth>256*2 or lgth1>256:
            raise ValueError(u'写入数据太长 %d/2，一条APDU最多允许256字节' % lgth)
        else:
            data1 = a2b(data)
            if len(data1)%8:
                padding = '\xFF' * (8-len(data1)%8)
                data1 = data1 + padding
            des = DES.new(a2b(key), DES.MODE_ECB, None)
            cipher = b2a( des.encrypt(a2b(data1)) )

            apdu = 'B'+cipher[-2] + 'B'+cipher[-1] + '%.4X'%(start&0xFFFF) + '%.2X'%(len(cipher)-1) + cipher[:-2]
            return api_pcsc.send(apdu, info='Write Flash, %d bytes, %s' % (lgth/2, data))

    def checkdata(self, start, end, crc, expectSW='9000'):
        return api_pcsc.send('BF42000006%.4X%.4X%s' % (start&0xFFFF, end&0xFFFF, crc), expectSW=expectSW, info='Check Data')

    def request(self):
        return api_pcsc.send('BF48020020', info='Read Factory Information')

    def parseatr(self, atr=ATR):
        if len(atr)==len(ATR) and atr[:20]==ATR[:20] and atr[28:30]==ATR[28:30]:
            status = atr[-2:]
            return STATUS.get(status, 'Unknown last character %s in ATR, check your card please' % status)
        else:
            return 'Unknown ATR, check your card please'


class TestCase_CIU98428F_Bootloader(api_unittest.TestCase):
    ''' 检测CIU98428F的FLASH良品率 '''

    def setUp(self):
        ''' the testing framework will automatically call for us when we run the test
            
            setUp()和tearDown()会在调用test_XXXX()方法时都会被调用，即会被调用多次。

            unittest将new一个class instance，然后调用setUp()，再调用某个test_XXXX()f方法，再调用tearDown()方法。
            重复多次以执行所有test_XXXX()方法。
        '''
        api_pcsc.connectreader()
        self.bl = Bootloader()

    def tearDown(self):
        self.bl = None
        api_pcsc.disconnect()

    def test_parseatr(self):
        atr = api_pcsc.getatr()
        self.assertEqual(atr, ATR)

        status = self.bl.parseatr(atr)
        self.assertEqual(status, STATUS.get('00', None))

    def test_verifypin(self):
        bl = self.bl
        bl.verifypin()
        pin = PIN
        wrongpin = ''.join(['%X'%((~int(x, 16))&0x0F) for x in pin])
        bl.verifypin(pin=wrongpin, expectSW='630E')
        bl.verifypin()

    def test_changpin(self):
        bl = self.bl
        bl.verifypin()
        newpin = ''.join(['%X'%((~int(x, 16))&0x0F) for x in PIN])
        bl.verifypin(pin=newpin, expectSW='630E')
        bl.verifypin()

        bl.changepin(PIN, newpin)
        bl.verifypin(pin=newpin, expectSW='9000')
        bl.verifypin(pin=PIN, expectSW='630E')
        bl.verifypin(pin=newpin, expectSW='9000')

        bl.changepin(newpin, PIN)
        bl.verifypin(pin=PIN, expectSW='9000')
        bl.verifypin(pin=newpin, expectSW='630E')
        bl.verifypin(pin=PIN, expectSW='9000')

    def test_changekey(self):
        # to do
        pass

    def test_erasepage(self):
        bl = self.bl
        bl.verifypin()

        # 注意：用户代码区不应包含 Loader 区高段，即 0x0006_9000~0x0006_AFFF 区域
        #
        # crc1 = api_crc.crc16('\xFF'*0x100, 0xFFFF)
        # crc2 = crc1[2:] + crc1[:2]

        # randomly select 10 pages to erase
        start, stop = 0x200/PAGESIZE, (0x69000/PAGESIZE)-1
        for i in range(10):
            j = random.randint(start, stop)
            bl.erasepage(j, j) # erase No.j page
            # bl.checkdata(j*2, j*2, '%.4X' % ((~int(crc1,16))&0xFFFF), expectSW='6500')
            # bl.checkdata(j*2, j*2, crc1)

    def test_write(self):
        bl = self.bl
        bl.verifypin()

        # 注意：用户代码区不应包含 Loader 区高段，即 0x0006_9000~0x0006_AFFF 区域
        #
        # randomly select 10 pages to erase
        start, stop = 0x200/PAGESIZE, (0x69000/PAGESIZE)-1
        for i in range(start, start+10, 1):
            bl.erasepage(i, i)
            bl.plaindownload(i*2, ('%.2X'%(random.randint(0,255)))*(PAGESIZE/2))
            bl.plaindownload(i*2+1, ('%.2X'%(random.randint(0,255)))*(PAGESIZE/2))

    def test_writeall(self):
        bl = self.bl
        bl.verifypin()

        # 注意：用户代码区不应包含 Loader 区高段，即 0x0006_9000~0x0006_AFFF 区域
        #
        # randomly select 10 pages to erase
        start, stop = 0x200/PAGESIZE, (0x69000/PAGESIZE-1)
        for i in range(start, stop, 1):
            bl.erasepage(i, i)
            bl.plaindownload(i*2, ('%.2X'%(random.randint(0,255)))*(PAGESIZE/2))
            bl.plaindownload(i*2+1, ('%.2X'%(random.randint(0,255)))*(PAGESIZE/2))



#----------------------------------------------------------------------------
def main():
    classes = (
        TestCase_CIU98428F_Bootloader,
        )
    testsuite = unittest.TestSuite([api_unittest.TestLoader().loadTestsFromTestCase(clz) for clz in classes])
    title = u'CIU98428F_Bootloader'
    description = u'通过CIU98428F自带的bootloader，对其样卡的FLASH做压力测试'
    path = os.path.abspath(__file__[:-3]+'.html')
    level = logging.DEBUG # 输入日记的多少, DEBUG时最多 INFO/ERROR/CRITICAL
    verbosity = 0 # 命令行窗口的输出详细程度 0/1/2 从少到多 设定为2时可以调试一些非测试案例出错的情况

    testresult = api_unittest.htmlunittest(testsuite, title, description, path, level, verbosity)
    webbrowser.open('file://'+path)

#----------------------------------------------------------------------------
if __name__ == '__main__':
    main()

