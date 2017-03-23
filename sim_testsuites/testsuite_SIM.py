#!/usr/env python
# -*- coding: utf-8 -*-

""" 检测SIM数据格式是否符合电信规范

This script will check if personalization data compliants with customer requirment.

__author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
__date__ = "Aug 2016"
__version__ = "0.1.0"

Copyright 2016 XH Smart Card Co,. Ltd
Author: wg@china-xinghan.com
"""

import logging, traceback, string, unittest, sets ,os ,collections
import api_pcsc
import api_util
import api_unittest
import api_validators
import api_gp
import api_tlv
import api_config
import api_unittest
import ui_client
import api_print
import MySQLdb
import api_unittest
import ui_notebook_sim

u = api_util.u
swap = api_util.swap
a2b = api_util.a2b
b2a = api_util.b2a

SW_NO_ERROR = '9000'
SW_FILE_NOT_FOUND = '6A82'
SW_FILE_NOT_FOUND_2G = '9404' # SIM卡的'文件未找到' SW是9404，不是6A82
SW_PIN1_DISABLED = '6984'
SW_PIN1_BLOCK = '6983'

Printer = ui_notebook_sim.Printer

FID = {
    'MF' : '3F00',
    'EF_DIR' : '2F00',
    'EF_ICCID' : '2FE2',
    'DF_GSM' : '7F20',
    'DF_DCS1800' : '7F21',
    'EF_IMSI' : '6F07',
    'EF_ACC' : '6F78',
    'DF_ACC'  : '7FF0',
}

#--------------------------------------------------------------------------------------------
def isallhexdigits(s):
    ''' '0123456789abcdefABCDEF' '''
    return all([c in string.hexdigits for c in s])

def isalldigits(s):
    ''' '0123456789' '''
    return all([c in string.digits for c in s])
       
def verify_pin_data(pin):
    '''判断pin格式是否正确，如31313131FFFFFFFF'''
    s = pin.decode('hex')
    FF = '\xff'
    i = s.find(FF)
    if i == -1:  # 找不到填充
        return isalldigits(s)
    else:
        if isalldigits(s[:i]):
            for c  in s[i:]:
                 if c != FF :
                    return False
            return True
        else:
            return False
            

def verify_puk_data(s):
    '''判断pin格式是否正确，如3139323430353331'''
    s = s.decode("hex")
    return isalldigits(s)
        

#----------------------------------------------------------------------------      

#----------------------------------------------------------------------------
class Usim(object):
    ''' 一个模拟USIM卡的类，可通过该类的实例对USIM卡进行select, read binary, update record, verify PIN/ADM等操作

        2016/10/19 暂不支持逻辑通道
    '''

    def __init__(self):
        pass

    def reset(self):
        ''' Reset usim
            returns ATR
        '''
        atr = api_pcsc.reset()
        return atr

    def selectbyaid(self, aid, nofcp=False, control='00', expectSW=SW_NO_ERROR):
        ''' 根据FID选择文件
            ETSI TS 102 221 V12.0.0 (2014-12), 11.1.1 SELECT

            fid: 2字节的文件ID
            nofcp: 是否Return FCP template，默认为True，即不返回FCP模板数据
            control: Selection by AID control，可以是 '00', '01', '10', '11', 即'First or only', 'Last', 'Next', 'Previous'
        '''
        x = 0x0C if nofcp else 0x04
        dit = { '00' : 0, '01' : 1, '10' : 2, '11' : 3, }
        y = dit.get(control, 0)
        p2 = '%.2X' % ((x|y) &0xFF)

        apdu = '00A404'+p2+'%.2X'%(len(aid)/2) + aid
        return self.send(apdu, expectSW=expectSW)

    def select(self, fid, nofcp=False, expectSW=SW_NO_ERROR):
        ''' 根据FID选择文件
            ETSI TS 102 221 V12.0.0 (2014-12), 11.1.1 SELECT

            fid: 2字节的文件ID
            nofcp: 是否Return FCP template，默认为True，即不返回FCP模板数据
        '''
        if nofcp:
            apdu = '00A4000C02'+fid
        else:
            apdu = '00A4000402'+fid
        return self.send(apdu, expectSW=expectSW)

    def readrecord(self, recno, length, mode='04', expectSW=SW_NO_ERROR):
        ''' 读记录
            ETSI TS 102 221 V12.0.0 (2014-12), 11.1.5 READ RECORD

            recno: Record number
            length: Number of bytes to be read


            2016/10/19 暂不支持p2为SFI
        '''
        apdu = '00B2%.2X%s%.2X' % (recno&0xFF, mode, length&0xFF)
        return self.send(apdu, expectSW=expectSW)

    def readbinary(self, offset, length, expectSW=SW_NO_ERROR):
        ''' 读二进制
            ETSI TS 102 221 V12.0.0 (2014-12), 11.1.3 READ BINARY

            offset:
            length: Number of bytes to be read

            2016/10/19 暂不支持p1为SFI
        '''
        apdu = '00B0%.4X%.2X' % (offset&0xFFFF, length&0xFF)
        return self.send(apdu, expectSW=expectSW)

    def getusimaid(self, efdir='2F00', rid='A000000087', appcode='1002'):
        ''' 从 EF_DIR 中查找USIM应用，返回其AID
            ETSI TS 102 221 V12.0.0 (2014-12), 13.1 EFDIR

            ETSI TS 101 220 V10.3.0 (2011-05), Annex E (normative): Allocated 3GPP PIX numbers
        '''
        self.reset()
        self.select(FID['MF'])
        fid = efdir if efdir else FID['EF_DIR']
        r, sw = self.select(fid, nofcp=False, expectSW='')
        if sw==SW_NO_ERROR:
            fci = FileControlInformation(r)
            i, numberofrecords, recordlength = 0, fci.numberofrecords, fci.recordlength
            target = rid+appcode
            while i<numberofrecords:
                r, sw = self.readrecord(i+1, recordlength)
                lgth = (2 + int(r[2:4], 16)) * 2
                app = ApplicationTemplate(r[:lgth])
                if app.aid.startswith(target):
                    return app.aid

    def getisimaid(self, efdir='2F00', rid='A000000087', appcode='1004'):
        ''' 从 EF_DIR 中查找ISIM应用，返回其AID
            ETSI TS 102 221 V12.0.0 (2014-12), 13.1 EFDIR
        '''
        return self.getusimaid(efdir, rid, appcode)

    def verifypin(self, pin, index, expectSW=SW_NO_ERROR):
        ''' 
        '''
        length = len(pin)/2
        apdu = '002000%.2X%.2X%s' % (index&0xFF, length, pin)
        return self.send(apdu, expectSW=expectSW)
        
        
    def verifypuk(self, pukpin, expectSW=SW_NO_ERROR):
        ''' 
        '''
        apdu = '002C000110%s' %pukpin 
        return self.send(apdu, expectSW=expectSW)


    def disablepin(self, pin, index=1, expectSW=SW_NO_ERROR):
        ''' 
        '''
        length = len(pin)/2
        apdu = '002600%.2X%.2X%s' % (index&0xFF, length, pin)
        return self.send(apdu, expectSW=expectSW)

    def enablepin(self, pin, index=1, expectSW=SW_NO_ERROR):
        ''' 
        '''
        length = len(pin)/2
        apdu = '002800%.2X%.2X%s' % (index&0xFF, length, pin)
        return self.send(apdu, expectSW=expectSW)

    def send(self, apdu, expectData='', expectSW=SW_NO_ERROR):
        ''' 对pcsc send函数的简单封装，设定期望状态字为9000
        '''
        return api_pcsc.send(apdu, expectData='', expectSW=expectSW)

        

#----------------------------------------------------------------------------

#---------------------------------------------------------------------------- 
class TestCase_Prd_Data(api_unittest.TestCase):
    ''' Checks Prd if data from datacenter all right
    '''
    @classmethod
    def setUpClass(cls):
        cls.datas = api_config.get_mysql_dict()
        
    def setUp(self):
        pass

    def test_01_ICCID(self):    
        ''' 检查ICCID值是否符合规范
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06)，10.1.1	EF ICCID (ICC Identification)
            ITU-T Rec. E.118 (05/2006) ，
        '''
        k, L, MII = 'ICCID', 20, '98' 
        iccid = self.datas[k]
        mii = iccid[:2]
        # TODO Country Code within ICCID should be extracted and shown 
        self.assertEqual(len(iccid), L, '%s: %s 长度 %d 错误，应为 %d' % (k,iccid,len(iccid),L))
        self.assertEqual(mii, MII, '%s: %s MII %s 错误，应为%s' % (k,iccid,mii,MII))
        self.assertTrue(isallhexdigits(iccid), '%s: %s 值错误，应全部为0-9a-fA-F' % (k,iccid))
        if 'F' == iccid[-2]:
            pan = swap(iccid)[:-1]
            self.assertTrue(api_util.verifyluhn(pan), '%s: %s Luhn校验位错误' % (k,iccid))
        else: # 某些老SIM卡的ICCID不是19位+‘F，没有luhn校验位
            self.logger.warning('%s: %s 不符合ITU-T Rec. E.118规范，有可能是3GPP TS 11.11 V8.14.0中提及的旧格式。请联系数据中心确认。' % (k, v))
            self.assertTrue(isalldigits(iccid), '%s: %s 值错误，应全部为0-9' % (k,iccid))
            
    def test_02_IMSI(self):    
        ''' 检查IMSI值是否符合规范
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        imsi = self.datas['IMSI']
        self.assertEqual(len(imsi), 16, '') 
        self.assertEqual(imsi[1], '9', "wrong IMSI")
        self.assertTrue(isalldigits(imsi), '%s: %s 值错误，应全部为0-9' % ('IMSI', imsi))

    def test_03_PIN1(self):    
        ''' 检查数据PIN1值 
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        v = self.datas['PIN1']
        self.assertEqual(len(v), 16, '')
        # 值应当为 0x30-0x39 或 0xFF 
        self.assertTrue(verify_pin_data(v), "%s: %s 值错误，应全部为0-9' % ('PIN1', v)")
            
    def test_04_PUK1(self):
        ''' 检查数据PUK1值 
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        v = self.datas['PUK1']
        self.assertEqual(len(v), 16, '')
        # 值应当为 0x30-0x39
        self.assertTrue(verify_puk_data(v), "%s: %s 值错误，应全部为0-9' % ('puk1', v)")
        
    def test_05_PIN2(self):    
        ''' 检查数据PIN2值 
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        v = self.datas['PIN2']
        self.assertEqual(len(v), 16, '')
        self.assertTrue(verify_pin_data(v), "%s: %s 值错误，应全部为0-9' % ('PIN2', v)")
        
    def test_06_PUK2(self):    
        ''' 检查PUK2值是否符合规范
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        v = self.datas['PUK2']
        k, LENGTH, l = 'puk2', 16, len(v)
        self.assertTrue(l == LENGTH, '%s: %s 长度 %d 错误，应为 %d' % (k, v, l, LENGTH))
        self.assertTrue(isalldigits(a2b(v)), '%s: %s 值错误，应全部为30-39' % (k, v))
        # 值应当为 0x30-0x39
        self.assertTrue(verify_puk_data(v), 'wrong puk data')

    def test_07_ADM1(self):
        ''' 检查ADM1值是否符合规范
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        v = self.datas['ADM1']
        k, LENGTH, l = 'ADM1', 16, len(v)
        self.assertTrue(l == LENGTH, '%s: %s 长度 %d 错误，应为 %d' % (k, v, l, LENGTH))
        self.assertTrue(isallhexdigits(v), '%s: %s 值错误，应全部为0-9a-fA-F' % (k, v))
        b = a2b(v)
        template = string.ascii_letters + string.digits
        self.assertTrue(all([c in template for c in b]), "%s: %s 值错误，应全部为'0-9a-zA-Z'" % (k, v))


    def test_08_KI(self):    
        ''' 检查KI值是否符合规范
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        v = self.datas['KI']
        k, LENGTH, l = 'KI', 32, len(v)
        self.assertTrue(l == LENGTH, '%s: %s 长度 %d 错误，应为 %d' % (k, v, l, LENGTH))
        self.assertTrue(isallhexdigits(v), '%s: %s 值错误，应全部为0-9a-fA-F' % (k, v)) 
        
    def test_09_ACC1(self):    
        ''' 检查ACC1值是否符合规范
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        v = self.datas['ACC1']
        k ,LENGTH ,l = 'ACC1',4,len(v)
        self.assertTrue(l == LENGTH, '%s: %s 长度 %d 错误，应为 %d' % (k, v, l, LENGTH))
        self.assertTrue((int( v[:2], 16)&0x04) == 0, '%s: %s 值错误，第1字节&0x04应当为0' % (k, v)) 
        
    def test_10_OPC(self):    
        ''' 检查数据OPC值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        ''' 
        v = self.datas['OPC']
        self.assertEqual(len(v), 32, 'OPC值为 %d 长度不正确,应为32' % len(v))
        self.assertTrue(isallhexdigits(v),"OPC有非法字符,值为 %s " % v)      

    def test_11_IMSI_ASCII(self):
        ''' 检查数据IMSI_ASCII值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        ''' 
        v = self.datas['IMSI_ASCII']
        self.assertEqual(len(v), 30, 'IMSI_ASCII长度为%d不正确,应为30' % len(v) )

        #IMSI_ASCII转化 再比较
        imsi_hex = v.decode('hex')
        self.assertTrue(isalldigits(imsi_hex),"IMSI_ASCII有非法字符 , 值为 %s " % imsi_hex)
        imsi = api_util.swap(('9'+imsi_hex))
        self.assertEqual(imsi, self.datas['IMSI'], "IMSI_ASCII转换为IMSI：%s 与IMSI %s不相符" % (imsi,self.datas['IMSI'] ))
        
    def test_12_KIC1(self):    
        ''' 检查数据KIC1值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        v = self.datas['KIC1']
        self.assertEqual(len(v), 32, 'KIC1长度为 %d 不正确,应为32' % len(v))
        self.assertTrue(isallhexdigits(v),"KIC1有非法字符，值为 %s " % v)

    def test_13_KID1(self):
        ''' 检查数据KID1值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        ''' 
        v = self.datas['KID1']
        self.assertEqual(len(v), 32, 'KID1长度为 %d 不正确,应为32' % len(v))        
        self.assertTrue(isallhexdigits(v),"KID1有非法字符,值为 %s " % v)

    def test_14_KIK1(self):    
        ''' 检查数据KIK1值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        v = self.datas['KIK1']
        self.assertEqual(len(v), 32, 'KIK1长度值为 %d 不正确,应为32' % len(v) )
        self.assertTrue(isallhexdigits(v), "KIK1有非法字符, 值为 %s " % v)
        
    def test_15_SYSPIN(self):    
        ''' 检查数据SYSPIN值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''            
        v = self.datas['SYSPIN']        
        self.assertEqual(len(v), 16, 'SYSPIN长度值为 %d 不正确,应为16' % len(v) )
        self.assertTrue(isallhexdigits(v),"SYSPIN有非法字符, 值为 %s " % v)
        
    def test_16_PRINT_ICCID(self):
        ''' 检查数据PRINT_ICCID值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''         
        v = self.datas['PRINT_ICCID']           
        self.assertEqual(len(v), 20, 'PRINT_ICCID长度值为 %d 不正确,应为20' % len(v) )        
        self.assertTrue(isallhexdigits(v),"PRINT_ICCID有非法字符, 值为 %s " % v)
        
        #ICCID置换后，再比较
        printiccid = api_util.swap(self.datas['ICCID'] )
        self.assertEqual(v, printiccid, 'PRINT_ICCID : %s与ICCID转化后的值 ：%s不符' % (v,printiccid ))     

    def test_17_PRINT_PIN1(self):    
        ''' 检查数据PRINT_PIN1值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        ''' 
        v = self.datas['PRINT_PIN1']
        self.assertEqual(len(v), 4, 'PRINT_PIN1值为%d长度不正确,应为4' )
        self.assertTrue(isalldigits(v),"PRINT_PIN1有非法字符")
        #PIN1转化 再比较
        pin1 = self.datas['PRINT_PIN1'].encode('hex')           
        for i in range(len(pin1),len(self.datas['PIN1'])):
            pin1 = pin1+'F'
        self.assertEqual(self.datas['PIN1'],pin1, 'PRINT_PIN1转PIN1值为 %s ,与PIN1值为 %s 不符' % (pin1,self.datas['PIN1']) )    

    def test_18_PRINT_PUK1(self):    
        ''' 检查数据PRINT_PUK1值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''    
        v = self.datas['PRINT_PUK1']        
        self.assertEqual(len(v), 8, 'PRINT_PUK1长度为 %d 不正确,应为8' % len(v) ) 
        self.assertTrue(isalldigits(v), "PRINT_PUK1: %s 有非法字符" % v)
        
        #PUK1转化 再比较
        puk1 = self.datas['PUK1'] .decode('hex')
        self.assertEqual(v, puk1, 'PRINT_PUK1值为  %s 不正确,应为%s' %(v,puk1))          

    def test_19_PRINT_MSISDN(self): 
        ''' 检查数据PRINT_MSISDN值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''       
        v = self.datas['PRINT_MSISDN']          
        self.assertEqual(len(v), 12, 'PRINT_MSISDN长度值为 %d 不正确,应为32' % len(v) )        
        self.assertTrue(isalldigits(v),"PRINT_MSISDN: %s 有非法字符" % v)      


    def test_20_PRINT_HLR(self): 
        ''' 检查数据PRINT_HLR值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        ''' 
        v = self.datas['PRINT_HLR']   
        self.assertEqual(len(v), 2, 'PRINT_HLR值长度不正确,应为2' )   
        self.assertEqual(v[0], 'H', 'PRINT_HLR ：%s 不正确，首字符应为H' % v )  


    def test_21_PRINT_REGION(self):
        ''' 检查数据PRINT_REGION值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''      
        v = self.datas['PRINT_REGION']          
        self.assertEqual(len(v), 2, 'PRINT_REGION值长度不正确,应为2' )
        self.assertEqual(v[0], 'R', 'PRINT_REGION : %s 不正确首字符应为R' % v)
        
    def test_22_verify_dataslen(self):
        ''' 检查传进来的字典datas长度是否为21
        '''
        l = len(self.datas)
        self.assertEqual(l, 21, '传进来的字典长度为 %d 不正确，应为21' % l )
  

class TestCase_simcard_Data(api_unittest.TestCase):
    ''' Checks if data from datacenter all right
    '''
    @classmethod
    def setUpClass(cls):
        # connect datacenter to get datas
        api_pcsc.connectreader()
        cls.usim = Usim()  
        cls.datas = api_config.get_mysql_dict()
        
    def setUp(self):
        # select MF
        self.usim.select(FID['MF'], False, SW_NO_ERROR)    
        
    def test_01_ICCID(self):
        ''' 检查card内iccid和数据中心数据是否相等
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        lgth = 0x0a
        iccid = self.datas['ICCID']
        usim = self.usim
        usim.select(FID['EF_ICCID'], False, SW_NO_ERROR)
        cardiccid,sw = usim.readbinary(0, lgth, SW_NO_ERROR)
        self.assertEqual(cardiccid, iccid, "卡内iccid为%s ,与所查询的ICCID: %s不符" % (cardiccid, iccid)) 
        
   
    def test_02_IMSI(self):
        ''' 检查card内IMSI和数据中心数据是否相等
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        lgth = 0x09
        imsi = self.datas['IMSI']
        usim = self.usim
        v = self.datas['PIN1']
        index = 1;
        r, sw1 = usim.verifypin(v, index, expectSW='')
        if sw1 == SW_NO_ERROR:
            pass
        elif sw1==SW_PIN1_DISABLED:
            usim.enablepin(v,index)
            r, sw = usim.verifypin(v, index, expectSW='')            
            self.assertTrue(sw == SW_NO_ERROR, '校验PIN1失败，sw为 %s' % sw )          
        else:
            self.fail()        
        usim.select(FID['DF_GSM'], False, SW_NO_ERROR)
        usim.select(FID['EF_IMSI'], False, SW_NO_ERROR)
        cardimsi,sw = usim.readbinary(0, lgth, SW_NO_ERROR)
        self.assertTrue(cardimsi[:2] == '08', "imsi 的第一字节为：%s,不等于08" % cardimsi[:2]) 
        self.assertEqual(cardimsi[2:], imsi, "卡内数据imsi为%s,与所查询的的IMSI:%s不符" % (cardimsi[2:],imsi))
        if sw1 == SW_PIN1_DISABLED:
            usim.disablepin(v)
        else :
            pass
        
        
    def test_03_PIN1(self):
        ''' 检查card内数据PIN1值是否正确
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        usim = self.usim
        v = self.datas['PIN1']
        index = 1;
        r, sw = usim.verifypin(v, index, expectSW='')
        if sw == SW_NO_ERROR:
            self.assertTrue(r=='')
        elif sw==SW_PIN1_DISABLED:
            usim.enablepin(v,index)
            assertTrue
            r, sw = usim.verifypin(v, index, expectSW='')
            self.assertTrue(cardimsi[:2] == '08', "imsi 的第一字节为：%s,不等于08" % cardimsi[:2]) 
            usim.disablepin(v)
        else:
            self.fail()
    
    def test_04_PUK1(self):
        ''' 检查card内数据PUK
            让pin连续输入错误锁死，输入PUK值恢复
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        v = self.datas['PUK1'] 
        c = self.datas['PIN1']
        k, LENGTH, l= 'puk1', 16, len(v)
        usim = self.usim       
        index = 1;
        wrongpin = "1234567891234567"
        r, sw1 = usim.verifypin(c, index, expectSW='')
        if sw1 == SW_NO_ERROR:
            self.assertTrue(r=='')
        elif sw1 == SW_PIN1_DISABLED:
            usim.enablepin(c,index)
            r, sw = usim.verifypin(c, index, expectSW='')
            self.assertTrue(sw == SW_NO_ERROR, '校验PIN1失败，sw为 %s' % sw )    
        else:
            self.fail()

        self.assertTrue(l==LENGTH, '%s: %s 长度 %d 错误，应为 %d' % (k, v, l, LENGTH))
        self.assertTrue(isalldigits(a2b(v)), '%s: %s 值错误，应全部为30-39' % (k, v))      
        while 1 :
            r, sw = usim.verifypin(wrongpin, index, expectSW='')  
            if sw == SW_PIN1_BLOCK :
                break
        r, sw = usim.verifypuk( v + c, expectSW='')
        self.assertTrue(sw == SW_NO_ERROR, '卡内数据puk1与所查询的不符合')  
        if sw1 == SW_PIN1_DISABLED:
            usim.disablepin(c)
        else:
            pass
        
     
       
    def test_05_PIN2(self): 
        ''' 检查card内数据PIN2值是否正确
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        usim = self.usim
        v = self.datas['PIN2']
        index = 2 
        r, sw = usim.verifypin(v, index, expectSW='')
        self.logger.info("pin2 = %s",r)
        if sw==SW_NO_ERROR:
            self.assertTrue(r=='') 
        elif sw==SW_PIN1_DISABLED:
            usim.enablepin(v,index)
            r, sw = usim.verifypin(v, index, expectSW='')
            self.assertTrue(sw == SW_NO_ERROR, "wrong pin,sw:%s" % sw) 
            usim.disablepin(v)
        else:
            self.fail()
            
    def test_06_PUK2(self):  
        ''' 检查PUK2值是否符合规范
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        pass
            
        
    
    def test_07_ADM1(self):
        ''' 检查ADM1值是否符合规范
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        pass


    def test_08_KI(self):    
        ''' 检查KI值是否符合规范
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        pass
        
    def test_09_ACC1(self):    
        ''' 检查ACC1值是否符合规范
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
            pin1的校验对ACC1无影响
        '''
        lgth = 0x02
        acc = self.datas['ACC1']
        usim = self.usim  
        usim.select(FID['DF_ACC'], False, SW_NO_ERROR)
        usim.select(FID['EF_ACC'], False, SW_NO_ERROR)
        cardacc, sw = usim.readbinary(0, lgth, SW_NO_ERROR)
        self.assertEqual(cardacc, acc, "卡内数据acc1: %s与所查询的acc1: %s不符" %(cardacc, acc) )
        
        
        
    def test_10_OPC(self):    
        ''' 检查数据OPC值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        ''' 
        pass
        
    def test_11_IMSI_ASCII(self):
        ''' 检查数据IMSI_ASCII值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        ''' 
        pass
        
    def test_12_KIC1(self):    
        ''' 检查数据KIC1值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        pass
        
    def test_13_KID1(self):
        ''' 检查数据KID1值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        ''' 
        pass
        
    def test_14_KIK1(self):    
        ''' 检查数据KIK1值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''
        pass
        
    def test_15_SYSPIN(self):    
        ''' 检查数据SYSPIN值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''            
        pass
        
    def test_16_PRINT_ICCID(self):    
        ''' 检查数据PRINT_ICCID值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''         
        pass
        
    def test_17_PRINT_PIN1(self):    
        ''' 检查数据PRINT_PIN1值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        ''' 
        pass
               
    def test_18_PRINT_PUK1(self):    
        ''' 检查数据PRINT_PUK1值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''    
        pass

    def test_19_PRINT_MSISDN(self): 
        ''' 检查数据PRINT_MSISDN值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''       
        pass

    def test_20_PRINT_HLR(self):    
        ''' 检查数据PRINT_HLR值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        ''' 
        pass


    def test_21_PRINT_REGION(self):
        ''' 检查数据PRINT_REGION值
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06) 
        '''  
        pass
        
class TestCase_Print(api_unittest.TestCase):
    '''根据数据生成虚拟版面，用于检查卡面打印是否正常'''
    
    @classmethod
    def setUpClass(cls):          
        cls.datas = api_config.get_mysql_dict() 
        cls.w, cls.h = Printer.getwidthheight()
        cls.x, cls.y = Printer.getsmallcardposition()
        cls.w1, cls.h1 = Printer.getsmallcardwidthheight()
        
    def setUp(self):
        assert hasattr(self, 'thread_instance')

    def post(self, texts, barcodes):
        self.thread_instance.PostSimUiEvent(texts, barcodes)
        
    def test_01_show_data(self):
        '''  show mysqldata
        '''  

        texts = [
                ('PIN1: '+self.datas['PRINT_PIN1'] + '    PUK1: '+self.datas['PRINT_PUK1'], (self.w*0.5, self.h*0.1)),
                (self.datas['PRINT_ICCID'][:10], (self.x+self.w1*0.3, self.y+self.h1*0.1)),
                (self.datas['PRINT_HLR'],        (self.x+self.w1*0.6, self.y+self.h1*0.3)),
                (self.datas['PRINT_ICCID'][10:], (self.x+self.w1*0.3, self.y+self.h1*0.6)),
                (self.datas['PRINT_ICCID'][:-1] +'  '+ self.datas['PRINT_HLR']+' '+ self.datas['PRINT_REGION'], (self.w*0.1, self.h*0.9)),
                ]
        barcodes = [
                # 内容、位置、编码格式
                (self.datas['PRINT_ICCID'][:-1], (self.w*0.1, self.h*0.6), 'CODE128'),
                ]

        self.post(texts, barcodes)
        

        
