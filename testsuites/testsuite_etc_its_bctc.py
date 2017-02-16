#!/usr/env python
# -*- coding: utf-8 -*-

""" 交通部科学院（ITS）的ETC卡测试在BCTC的物理特性测试，包括冷热复位、PPS波特率、时钟停止等

This script will check if personalization data compliants with customer requirment.

__author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
__date__ = "Aug 2016"
__version__ = "0.1.0"

Copyright 2016 XH Smart Card Co,. Ltd

Author: wg@china-xinghan.com
"""

import logging, os, webbrowser, unittest, urllib

import api_pcsc
import api_gp
import api_util
import api_unittest


#----------------------------------------------------------------------------
u = api_util.u

#----------------------------------------------------------------------------
class Applet_ETC_ITS_BCTC(object):
    ''' Fake ETC applet '''

    def getcappath(self):
        cap = "ETC_ITS_BCTC.cap"
        return api_unittest.getcappath(cap)

    def getaids(self):
        instance, pkg, applet = 'A00000000386980701', 'A000000003869807', 'A00000000386980701'
        return instance, pkg, applet

    def select(self):
        instance, pkg, applet = self.getaids()
        return api_gp.select(instance)

    def changepin(self, old, new):
        data = old+'FF'+new
        lc = len(data) / 2
        return api_pcsc.send('805E0100%.2X%s' % (lc, data), expectSW='9000')

#----------------------------------------------------------------------------
class Cloud4700(object):
    ''' CLOUD 47X0 F REFERENCE MANUAL, <CLOUD_4700F_um用户手册.pdf>

        6.1.3. PAPDU_ESCAPE_CMD

        6.3. Escape commands for the CLOUD 47x0 F
            6.3.1. Sending Escape commands to CLOUD 47x0 F
                CLA     INS     P1      P2      Lc      Data_in     Le
                0xFF    0xCC    0x00    0x00    YY      ...         XX

            6.3.2. Escape command codes
            6.3.3. Common for Contact and Contactless Interfaces

                ESCAPE COMMAND              ESCAPE CODE
                READER_SETMODE              0x01
                READER_GETMODE              0x02
                READER_GETIFDTYPE           0x12
                READER_LED_CONTROL          0x19
                READER_GETINFO_EXTENDED     0x1E
                READER_LED_CONTROL_BY_FW    0xB2
                READER_RDWR_USR_AREA        0xF0
                READER_GENERIC_ESCAPE       FF 70 04 E6 XX

            6.3.5. Specific for Contact Interface
                ESCAPE COMMAND Escape code
                CONTACT_GET_SET_PWR_UP_SEQUENCE 0x04
                CONTACT_EMV_LOOPBACK            0x05
                CONTACT_EMV_SINGLEMODE          0x06
                CONTACT_EMV_TIMERMODE           0x07
                CONTACT_APDU_TRANSFER           0x08
                CONTACT_DISABLE_PPS             0x0F
                CONTACT_EXCHANGE_RAW            0x10
                CONTACT_GET_SET_CLK_FREQUENCY   0x1F
                CONTACT_CONTROL_ATR_VALIDATION  0x88
                CONTACT_GET_SET_MCARD_TIMEOUT   0x85
                CONTACT_GET_SET_ETU             0x80
                CONTACT_GET_SET_WAITTIME        0x81
                CONTACT_GET_SET_GUARDTIME       0x82
                CONTACT_READ_INSERTION_COUNTER  READER_ESCAPE_GENERIC (0x00)
    '''


    ESCAPE = 'FFCC0000'
    READER_NAME = 'Identiv uTrust 4700 F Contact Reader 0'

    def enable_class(self, a, b, c):
        ''' 6.3.5.1. CONTACT_GET_SET_PWR_UP_SEQUENCE
        '''
        bitmap = 0
        bitmap = bitmap|0x01 if a else bitmap&0xFE
        bitmap = bitmap|0x02 if b else bitmap&0xFD
        bitmap = bitmap|0x04 if c else bitmap&0xFB
        apdu = '04' + '09' + '%.2X'%(bitmap&0xFF)
        return api_pcsc.send(self.ESCAPE + '03' + apdu)

    def enable_all_classes(self):
        ''' 6.3.5.1. CONTACT_GET_SET_PWR_UP_SEQUENCE
        '''
        apdu = '04' + '09' + '07'
        return api_pcsc.send(self.ESCAPE + '03' + apdu)


class TestCase_ETC_ITS_BCTC(api_unittest.TestCase):
    ''' 检测 javacard.framework.JCSystem 
    '''

    @classmethod
    def setUpClass(cls):
        # delete, load, install
        etc = Applet_ETC_ITS_BCTC()
        instance, pkg, applet = etc.getaids()

        api_pcsc.connectreader(Cloud4700.READER_NAME) # 指明读卡器名字，因为目前只有4700可以通过APDU方式设定各类电压是否支持
        api_gp.card()
        api_gp.auth()
        api_gp.deleteaid(pkg, True, expectSW='') # omit delete result
        api_gp.upload(etc.getcappath(), pkg)
        api_gp.install(instance, pkg, applet)

        cloud = Cloud4700()
        cloud.enable_all_classes()
        api_pcsc.reset()

        cls.etc = etc
        cls.cloud = cloud

    @classmethod
    def tearDownClass(cls):
        instance, pkg, applet = cls.etc.getaids()
        api_pcsc.connectreader(Cloud4700.READER_NAME)
        api_gp.card()
        api_gp.auth()
        api_gp.deleteaid(pkg, True, expectSW='9000')
        cls.etc = None

        cls.cloud.enable_all_classes()
        cls.cloud = None

        api_pcsc.disconnect()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_0_hasTC1(self):
        ''' ATR应包含TC1，以解决THD88不支持接收11.8ETU字符的问题
        '''
        # check ATR to determine if it is THD88 chip,
        # if yes, test if TC1 included in ATR
        atr = api_pcsc.getatr()
        ts = int(atr[2:4], 16)
        hasta1 = True if ts&0x01 else False
        hastb1 = True if ts&0x02 else False
        hastc1 = True if ts&0x04 else False
        
        self.logger.info('ATR: ' + atr)
        if hasta1:
            offset = 2
            offset = offset+1 if hasta1 else offset
            offset = offset+1 if hastb1 else offset
            offset = offset * 2
            tc1 = atr[offset:offset+2]

            self.logger.info('TC1: ' + tc1)
            self.logger.info('ATR已包含TC1，可以解决THD88不支持接收11.8ETU字符的问题')
        else:
            self.logger.info('ATR应包含TC1，否则BCTC测试ETC时会出现THD88不支持接收11.8ETU字符的问题')
            self.fail('ATR应包含TC1，否则BCTC测试ETC时会出现THD88不支持接收11.8ETU字符的问题')

        if hastc1:
            etc, cloud = self.etc, self.cloud
            api_pcsc.reset(cold=True)
            etc.select()
            api_pcsc.reset(cold=False)
            etc.select()

    def test_1_EnhancedBaudrate(self):
        ''' *****测试案例－增强速率测试*****
        '''
        # test if PPS1=00, 11, 94, 95, 96 are all supported

        # cold reset
        # ATR
        # PPSS
        # select
        # warm reset
        # ATR
        # PPSS
        # select
        pass

    def test_2_Voltage_Class_A(self, a=True, b=False, c=False):
        ''' *****测试案例－电压限值测试 - 5V *****
        '''
        etc, cloud = self.etc, self.cloud
        
        api_pcsc.reset()
        r, sw = cloud.enable_class(a=a, b=b, c=c) # enable Class A only
        self.assertEqual(sw, '9000')

        # 卡复位成功，ATR: 3B789400000073C84013009000
        # Select 应用:00 A4 04 00 09   Data:A00000000386980701   SW:9000

        # 设置VCC=4500mV successful!
        # 卡复位，ATR: 3B789400000073C84013009000 ///////////////////////////////////////热复位
        # 选择应用失败!
        # 设置VCC=5500mV successful!
        # 卡复位，ATR: 3B789400000073C84013009000
        # Select 应用:00 A4 04 00 09   Data:A00000000386980701   SW:9000
        # Change PIN:80 5E 01 00 05  Data:1234FF0000  SW：9000
        # Change PIN:80 5E 01 00 05  Data:0000FF1234  SW：9000
        # 对应以下测试

        api_pcsc.reset()
        etc.select()

        api_pcsc.reset(cold=False) # 目前无法设置电压为4500mV，暂时用5V热复位替代
        etc.select()

        api_pcsc.reset(cold=False) # 目前无法设置电压为5500mV，暂时用5V热复位替代
        etc.select()
        etc.changepin('1234', '0000')
        etc.changepin('0000', '1234')

        # BCTC测试结束
        # 下面是另外增加的测试
        api_pcsc.reset()
        etc.select()

        api_pcsc.reset(cold=True) # 目前无法设置电压为4500mV，暂时用5V冷复位替代
        etc.select()

        api_pcsc.reset(cold=True) # 目前无法设置电压为5500mV，暂时用5V冷复位替代
        etc.select()
        etc.changepin('1234', '0000')
        etc.changepin('0000', '1234')

    def test_3_Voltage_Class_B(self):
        ''' *****测试案例－电压限值测试 - 3V *****
        '''

        # 成功初始化Log过程
        # 卡复位成功，ATR: 3B789400000073C84013009000
        # Select 应用:00 A4 04 00 09   Data:A00000000386980701   SW:9000

        # 设置VCC=2700mV successful!
        # 卡复位，ATR: 3B789400000073C84013009000 ///////////////////////////////////////热复位
        # 选择应用失败!
        # 设置VCC=3300mV successful!
        # 卡复位，ATR: 3B789400000073C84013009000
        # Select 应用:00 A4 04 00 09   Data:A00000000386980701   SW:9000
        # Change PIN:80 5E 01 00 05  Data:1234FF0000  SW：9000
        # Change PIN:80 5E 01 00 05  Data:0000FF1234  SW：9000
        self.test_2_Voltage_Class_A(a=False, b=True, c=False)

    def test_4_Voltage_Class_C(self):
        ''' *****测试案例－电压限值测试 - 1.8V *****
        '''

        # 成功初始化Log过程
        # 卡复位成功，ATR: 3B789400000073C84013009000
        # Select 应用:00 A4 04 00 09   Data:A00000000386980701   SW:9000

        # 设置VCC=1620mV successful!
        # 卡复位，ATR: 3B789400000073C84013009000 ///////////////////////////////////////热复位
        # 选择应用失败!
        # 设置VCC=1980mV successful!
        # 卡复位，ATR: 3B789400000073C84013009000
        # Select 应用:00 A4 04 00 09   Data:A00000000386980701   SW:9000
        # Change PIN:80 5E 01 00 05  Data:1234FF0000  SW：9000
        # Change PIN:80 5E 01 00 05  Data:0000FF1234  SW：9000
        self.test_2_Voltage_Class_A(a=False, b=False, c=True)

#----------------------------------------------------------------------------
def main():
    classes = (
        TestCase_ETC_ITS_BCTC,
        )
    testsuite = unittest.TestSuite([api_unittest.TestLoader().loadTestsFromTestCase(clz) for clz in classes])
    title = u'ETC ITS BCTC'
    description = u'交通部科学院（ITS）的ETC卡测试在BCTC的物理特性测试，包括冷热复位、PPS波特率、时钟停止等'
    path = os.path.abspath('testsuite_etc_its_bctc.html')
    level = logging.INFO # 输入日记的多少, DEBUG时最多 INFO/ERROR/CRITICAL
    verbosity = 0 # 命令行窗口的输出详细程度 0/1/2 从少到多 设定为2时可以调试一些非测试案例出错的情况

    testresult = api_unittest.htmlunittest(testsuite, title, description, path, level, verbosity)
    webbrowser.open('file:'+urllib.pathname2url(path))

#----------------------------------------------------------------------------
if __name__ == '__main__':
    main()

