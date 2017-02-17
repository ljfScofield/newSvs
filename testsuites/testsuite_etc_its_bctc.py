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

    PIN = '1234'

    def getcappath(self):
        cap = "ETC_ITS_BCTC.cap"
        return api_unittest.getcappath(cap)

    def getaids(self):
        instance, pkg, applet = 'A00000000386980701', 'A000000003869807', 'A00000000386980701'
        return instance, pkg, applet

    def select(self):
        instance, pkg, applet = self.getaids()
        return api_gp.select(instance)

    def verifypin(self, pin):
        lc = len(pin) / 2
        return api_pcsc.send('00200000%.2X%s' % (lc, pin), expectSW='9000', name='Verify PIN')

    def changepin(self, old, new):
        data = old+'FF'+new
        lc = len(data) / 2
        return api_pcsc.send('805E0100%.2X%s' % (lc, data), expectSW='9000', name='Change PIN')

    def readbinary(self):
        return api_pcsc.send('00B0950000', expectSW='9000', name='Read Binary')

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
        return api_pcsc.send(self.ESCAPE + '03' + apdu, expectSW='9000', name='CONTACT_GET_SET_PWR_UP_SEQUENCE')

    def enable_all_classes(self):
        ''' 6.3.5.1. CONTACT_GET_SET_PWR_UP_SEQUENCE
        '''
        apdu = '04' + '09' + '07'
        return api_pcsc.send(self.ESCAPE + '03' + apdu, expectSW='9000', name='CONTACT_GET_SET_PWR_UP_SEQUENCE')

    def disable_pps(self):
        ''' 6.3.5.6. CONTACT_DISABLE_PPS
        '''
        apdu = '0F' + '01'
        return api_pcsc.send(self.ESCAPE + '02' + apdu, expectSW='9000', name='CONTACT_DISABLE_PPS')

    def enable_pps(self):
        ''' 6.3.5.6. CONTACT_DISABLE_PPS
        '''
        apdu = '0F' + '00'
        return api_pcsc.send(self.ESCAPE + '02' + apdu, expectSW='9000', name='CONTACT_ENABLE_PPS')

    def exchange_raw(self, rawdata, expected_length):
        ''' 6.3.5.7. CONTACT_EXCHANGE_RAW
        '''
        lgth = len(rawdata) / 2
        msb1, lsb1 = '%.2X'%((lgth>>8)&0xFF), '%.2X'%(lgth&0xFF)
        msb2, lsb2 = '%.2X'%((expected_length>>8)&0xFF), '%.2X'%(expected_length&0xFF)
        apdu = '10' +lsb1+msb1 +lsb2+msb2 + rawdata
        return api_pcsc.send(self.ESCAPE + '%.2X'%(len(apdu)/2) + apdu, expectSW='9000', name='CONTACT_EXCHANGE_RAW')

    def get_etu(self):
        ''' 6.3.5.11. CONTACT_GET_SET_ETU
        '''
        apdu = '80' + '00'
        return api_pcsc.send(self.ESCAPE + '02' + apdu, expectSW='9000', name='CONTACT_GET_ETU')

    def set_etu(self, etu):
        ''' 6.3.5.11. CONTACT_GET_SET_ETU
        '''
        apdu = '80' + '01' +'%.8X' % (etu&0xFFFFFFFF)
        return api_pcsc.send(self.ESCAPE + '%.2X'%(len(apdu)/2) + apdu, expectSW='9000', name='CONTACT_SET_ETU')

    def set_clock_divison(self, divison):
        ''' 6.3.5.8. CONTACT_GET_SET_CLK_FREQUENCY
                DIVISOR VALUE   SCCLK Frequency
                12              4 MHz
                10              4.8 MHz
                8               6 MHz
                7               6.8 MHz
                6               8 MHz
                5               9.6 MHz
                4               12 MHz
                3               16 MHz
        '''
        apdu = '1F' + '%.2X' % (divison&0xFF)
        return api_pcsc.send(self.ESCAPE + '02' + apdu, expectSW='9000', name='CONTACT_SET_CLK_FREQUENCY')

    def get_clock_divison(self):
        ''' 6.3.5.8. CONTACT_GET_SET_CLK_FREQUENCY
        '''
        apdu = '1F' + 'FF'
        return api_pcsc.send(self.ESCAPE + '02' + apdu, expectSW='9000', name='CONTACT_GET_CLK_FREQUENCY')


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
        cloud.set_clock_divison(4) # restore to 4.8 MHz
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
        cls.cloud.enable_pps()
        cls.cloud.set_clock_divison(4) # restore to 4.8 MHz
        cls.cloud = None

        api_pcsc.disconnect()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_ClockStop_Current_Consumption_Class_A(self):
        ''' 5V，时钟停止状态下电流测试
        '''
        self.logger.info('规范要求卡片在5V、时钟停止状态下电流最大值不得大于200uA')
        self.logger.info('请务必测试确认卡片已支持ClockStop')
        self.fail('读卡器上无法完成该项测试, 请用电压表完成该项测试')

    def test_ClockStop_Current_Consumption_Class_B(self):
        ''' 3V，时钟停止状态下电流测试
        '''
        self.logger.info('规范要求卡片在3V、时钟停止状态下电流最大值不得大于100uA')
        self.logger.info('请务必测试确认卡片已支持ClockStop')
        self.fail('读卡器上无法完成该项测试, 请用电压表完成该项测试')

    def test_ClockStop_Current_Consumption_Class_C(self):
        ''' 1.8V，时钟停止状态下电流测试
        '''
        self.logger.info('规范要求卡片在1.8V、时钟停止状态下电流最大值不得大于100uA')
        self.logger.info('请务必测试确认卡片已支持ClockStop')
        self.fail('读卡器上无法完成该项测试, 请用电压表完成该项测试')

    def test_Idle_Current_Consumption_Class_A(self):
        ''' 5V，空闲状态下电流测试
        '''
        self.logger.info('规范要求卡片在5V、空闲状态下电流最大值不得大于200uA')
        self.logger.info('请务必测试确认卡片已支持ClockStop')
        self.fail('读卡器上无法完成该项测试, 请用电压表完成该项测试')

    def test_Idle_Current_Consumption_Class_B(self):
        ''' 3V，空闲状态下电流测试
        '''
        self.logger.info('规范要求卡片在3V、空闲状态下电流最大值不得大于200uA')
        self.logger.info('请务必测试确认卡片已支持ClockStop')
        self.fail('读卡器上无法完成该项测试, 请用电压表完成该项测试')

    def test_Idle_Current_Consumption_Class_C(self):
        ''' 1.8V，空闲状态下电流测试
        '''
        self.logger.info('规范要求卡片在1.8V、空闲状态下电流最大值不得大于200uA')
        self.logger.info('请务必测试确认卡片已支持ClockStop')
        self.fail('读卡器上无法完成该项测试, 请用电压表完成该项测试')

    def test_ATR_PowerConsume_Class_A(self):
        ''' ATR过程中卡功耗(Class A)测试
        '''
        self.logger.info('该项测试要求测量5V电压下，时钟频率为4MHz和5MHz时，ATR期间的电流，请用电压表搭配转接板测量')
        self.logger.info('测试标准：卡在最大外部时钟频率下ATR的功耗不得大于10mA,在4MHz下ATR中的功耗不得大于8mA')
        self.fail('读卡器上无法完成该项测试, 请用电压表完成该项测试')

    def test_ATR_PowerConsume_Class_B(self):
        ''' ATR过程中卡功耗(Class B)测试
        '''
        self.logger.info('该项测试要求测量3V电压下，时钟频率为4MHz和5MHz时，ATR期间的电流，请用电压表搭配转接板测量')
        self.logger.info('测试标准：卡在最大外部时钟频率下ATR的功耗不得大于7.5mA,在4MHz下ATR中的功耗不得大于6mA')
        self.fail('读卡器上无法完成该项测试, 请用电压表完成该项测试')

    def test_ATR_PowerConsume_Class_C(self):
        ''' ATR过程中卡功耗(Class C)测试
        '''
        self.logger.info('该项测试要求测量1.8V电压下，时钟频率为4MHz和5MHz时，ATR期间的电流，请用电压表搭配转接板测量')
        self.logger.info('测试标准：卡在最大外部时钟频率下ATR的功耗不得大于5mA,在4MHz下ATR中的功耗不得大于4mA')
        self.fail('读卡器上无法完成该项测试, 请用电压表完成该项测试')

    def test_VPP(self):
        ''' VPP触点静态操作测试,A类卡（3G卡）
        '''
        self.logger.info('该项测试要求控制VPP引脚的开闭、电压，请用电压表搭配转接板测量')
        self.fail('读卡器上无法完成该项测试, 请用电压表完成该项测试')

    def test_TA196(self):
        ''' ATR应包含TA1，且大于等于0x96
        '''
        atr = api_pcsc.getatr()
        self.logger.info('ATR: ' + atr)

        ts = int(atr[2:4], 16)
        hasta1 = True if ts&0x01 else False
        self.assertTrue(hasta1, 'ATR应包含TA1')

        ta1 = atr[4:6]
        self.assertTrue(int(ta1, 16)>0x96, 'ATR应包含TA1')

    def test_hasTC1(self):
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

    def test_Electrical_Class_A(self):
        ''' 与电相关的参数(Class A)测试：应用选择的功耗应符合规范要求,Icc应在0mA至60mA范围内

                测试标准：
                应用选择的功耗应符合规范要求,Icc应在0mA至60mA范围内
        '''
        etc, cloud = self.etc, self.cloud
        api_pcsc.reset(cold=True)
        etc.select()
        etc.verifypin(etc.PIN)
        api_pcsc.reset(cold=False)
        etc.select()
        etc.verifypin(etc.PIN)

    def test_T0_Case2(self):
        ''' T=0命令方式二测试: 卡应能正确处理命令方式二
            测试标准：
            卡应能正确处理命令方式二

            成功初始化Log过程
            卡复位：ATR= 3B789600000073C84013009000
            Select Usim:00 A4 04 00 09   Data:A00000000386980701 SW:9000
            Read Binary:00 B0 95 00 00  SW:6A82
            Read Binary命令返回状态码错误! 
        '''
        etc, cloud = self.etc, self.cloud
        api_pcsc.reset(cold=True)
        etc.select()
        etc.readbinary()
        api_pcsc.reset(cold=False)
        etc.select()
        etc.readbinary()

    def test_ClockFrequency_4(self, clk=4):
        ''' 时钟频率范围测试：4 MHz
        '''
        etc, cloud = self.etc, self.cloud
        api_pcsc.reset(cold=True)

        dit_clk = {
                4 : 12,
                4.8 : 10,
                6 : 8,
                6.8 : 7,
                8 : 6,
                9.6 : 5,
                12 : 4,
                16 : 3,
                }
        divison = dit_clk[clk]
        cloud.set_clock_divison(divison)
        r, sw = cloud.get_clock_divison()
        self.assertEqual(r, '%.2X'%divison)

        api_pcsc.reset(cold=True)
        cloud.disable_pps()
        dit_pps = {
                '00': ('FF00FF', 0x174),
                '11': ('FF1011FE', 0x174),
                '94': ('FF10947B', 0x40),
                '95': ('FF10957A', 0x20),
                '96': ('FF109679', 0x10),
                #'97': ('FF109778', 0x08),
                }
        for k in sorted(dit_pps.keys()):
            pps, etu = dit_pps[k]
            api_pcsc.reset(cold=True)
            r, sw = cloud.exchange_raw(pps, len(pps)/2)
            self.assertEqual(r, pps)
            r, sw = cloud.set_etu(etu)
            self.assertEqual(r, '%.8X'%etu)
            etc.select()

            api_pcsc.reset(cold=False)
            r, sw = cloud.exchange_raw(pps, len(pps)/2)
            self.assertEqual(r, pps)
            r, sw = cloud.set_etu(etu)
            self.assertEqual(r, '%.8X'%etu)
            etc.select()

            self.logger.info('Clock Frequency %d, TA1 %s passed' % (clk, k))

    def test_ClockFrequency_48(self, clk=4.8):
        ''' 时钟频率范围测试：4.8 MHz
        '''
        self.test_ClockFrequency_4(clk=clk)

    def test_ClockFrequency_6(self, clk=6):
        ''' 时钟频率范围测试：6 MHz
        '''
        self.test_ClockFrequency_4(clk=clk)

    def test_ClockFrequency_68(self, clk=6.8):
        ''' 时钟频率范围测试：6.8 MHz
        '''
        self.test_ClockFrequency_4(clk=clk)

    def test_ClockFrequency_8(self, clk=8):
        ''' 时钟频率范围测试：8 MHz
        '''
        self.test_ClockFrequency_4(clk=clk)

    def test_ClockFrequency_96(self, clk=9.6):
        ''' 时钟频率范围测试：9.6 MHz
        '''
        self.test_ClockFrequency_4(clk=clk)

    def test_ClockFrequency_12(self, clk=12):
        ''' 时钟频率范围测试：12 MHz
        '''
        self.test_ClockFrequency_4(clk=clk)

    def test_ClockFrequency_16(self, clk=16):
        ''' 时钟频率范围测试：16 MHz
        '''
        self.test_ClockFrequency_4(clk=clk)

    def test_Delay_Between_PPS_Request_Response(self, pps1='00'):
        ''' 字符帧测试

            测试标准：传输的字符帧要符合ISO/IEC 7816-3[6]的要求,请结合MPScopeViewer软件进行判定

            PPS请求和响应之间的间隔应当大于4ETU
        '''
        etc, cloud = self.etc, self.cloud
        api_pcsc.reset(cold=True)
        cloud.disable_pps()

        dit = {
                '00': ('FF00FF', 0x174),
                '11': ('FF1011FE', 0x174),
                '94': ('FF10947B', 0x40),
                '95': ('FF10957A', 0x20),
                '96': ('FF109679', 0x10),
                #'97': ('FF109778', 0x08),
                }
        pps, etu = dit['94']
        api_pcsc.reset(cold=True)
        r, sw = cloud.exchange_raw(pps, len(pps)/2) # PPS请求和响应之间的间隔应当大于4ETU
        self.assertEqual(r, pps)
        r, sw = cloud.set_etu(etu)
        self.assertEqual(r, '%.8X'%etu)
        etc.select()

        api_pcsc.reset(cold=False)
        pps, etu = dit['95']
        r, sw = cloud.exchange_raw(pps, len(pps)/2) # PPS请求和响应之间的间隔应当大于4ETU
        self.assertEqual(r, pps)
        r, sw = cloud.set_etu(etu)
        self.assertEqual(r, '%.8X'%etu)
        etc.select()

        api_pcsc.reset(cold=False)
        pps, etu = dit['96']
        r, sw = cloud.exchange_raw(pps, len(pps)/2) # PPS请求和响应之间的间隔应当大于4ETU
        self.assertEqual(r, pps)
        r, sw = cloud.set_etu(etu)
        self.assertEqual(r, '%.8X'%etu)
        etc.select()

        api_pcsc.reset(cold=False)
        pps, etu = dit['11']
        r, sw = cloud.exchange_raw(pps, len(pps)/2) # PPS请求和响应之间的间隔应当大于4ETU
        self.assertEqual(r, pps)
        r, sw = cloud.set_etu(etu)
        self.assertEqual(r, '%.8X'%etu)
        etc.select()

        self.logger.info('PPS请求和响应之间的间隔应当大于4ETU，请使用Salea Logic测量确认')
        self.logger.info('注意：以上出现的PPS请求和响应的间隔必须全部测量确认')
        self.fail('PPS请求和响应之间的间隔应当大于4ETU，请使用Salea Logic测量确认')

    def test_9600bps(self, pps1='00'):
        ''' TA1=0x00
        '''
        etc, cloud = self.etc, self.cloud
        api_pcsc.reset(cold=True)
        cloud.disable_pps()

        dit = {
                '00': ('FF00FF', 0x174),
                '11': ('FF1011FE', 0x174),
                '94': ('FF10947B', 0x40),
                '95': ('FF10957A', 0x20),
                '96': ('FF109679', 0x10),
                #'97': ('FF109778', 0x08),
                }
        pps, etu = dit[pps1]

        # cold reset
        # ATR
        # PPSS
        # select
        # warm reset
        # ATR
        # PPSS
        # select
        api_pcsc.reset(cold=True)
        r, sw = cloud.exchange_raw(pps, len(pps)/2)
        self.assertEqual(r, pps)
        r, sw = cloud.set_etu(etu)
        self.assertEqual(r, '%.8X'%etu)
        etc.select()

        api_pcsc.reset(cold=False)
        r, sw = cloud.exchange_raw(pps, len(pps)/2)
        self.assertEqual(r, pps)
        r, sw = cloud.set_etu(etu)
        self.assertEqual(r, '%.8X'%etu)
        etc.select()

        cloud.enable_pps()
        api_pcsc.reset(cold=True)
        etc.select()
        api_pcsc.reset(cold=False)
        etc.select()

    def test_9600bps_TA1_11(self, pps1='11'):
        ''' TA1=0x11
        '''
        self.test_9600bps(pps1)

    def test_57600bps(self, pps1='94'):
        ''' TA1=0x94
        '''
        self.test_9600bps(pps1)

    def test_115200bps(self, pps1='95'):
        ''' TA1=0x95
        '''
        self.test_9600bps(pps1)

    def test_230400bps(self, pps1='96'):
        ''' TA1=0x96
        '''
        self.test_9600bps(pps1)

    #def test_460800bps(self, pps1='97'):
    #    ''' TA1=0x97 *****
    #    '''
    #    self.test_9600bps(pps1)

    def test_Voltage_Class_A(self, a=True, b=False, c=False):
        ''' 电压限值测试 - 5V
        '''
        etc, cloud = self.etc, self.cloud
        
        api_pcsc.reset()
        r, sw = cloud.enable_class(a=a, b=b, c=c) # enable Class A only

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

        api_pcsc.reset(cold=True)
        etc.select()

        api_pcsc.reset(cold=False) # 目前无法设置电压为4500mV，暂时用5V热复位替代
        etc.select()

        api_pcsc.reset(cold=False) # 目前无法设置电压为5500mV，暂时用5V热复位替代
        etc.select()
        old, new = etc.PIN, '0000'
        etc.changepin(old, new)
        etc.changepin(new, old)

        # BCTC测试结束
        # 下面是另外增加的测试
        api_pcsc.reset()
        etc.select()

        api_pcsc.reset(cold=True) # 目前无法设置电压为4500mV，暂时用5V冷复位替代
        etc.select()

        api_pcsc.reset(cold=True) # 目前无法设置电压为5500mV，暂时用5V冷复位替代
        etc.select()
        old, new = etc.PIN, '0000'
        etc.changepin(old, new)
        etc.changepin(new, old)

    def test_Voltage_Class_B(self):
        ''' 电压限值测试 - 3V
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
        self.test_Voltage_Class_A(a=False, b=True, c=False)

    def test_Voltage_Class_C(self):
        ''' 电压限值测试 - 1.8V
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
        self.test_Voltage_Class_A(a=False, b=False, c=True)

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

