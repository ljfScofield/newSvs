#!/usr/env python
# -*- coding: utf-8 -*-

""" 提供常见的各种数据（例如ICCID、IMSI等）的校验器Validator
    This module offers validators for common data used in smart card personalization.

    __author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
    __date__ = "Aug 2016"
    __version__ = "0.1.0"
    
    Copyright 2016 XH Smart Card Co,. Ltd
    
    Author: wg@china-xinghan.com
"""

import logging, traceback, string, unittest, sets
import api_util


a2b = api_util.a2b
b2a = api_util.b2a

def isallhexdigits(s):
    ''' '0123456789abcdefABCDEF' '''
    return all([c in string.hexdigits for c in s])

def isalldigits(s):
    ''' '0123456789' '''
    return all([c in string.digits for c in s])


class ValidatorException(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class Validator(object):

    KEY = 'KEY'

    def __init__(self):
        pass

    def dotest(self, datas):
        ''' 子类应当覆盖该方法，实现对value = datas[KEY]的校验
            datas应为一个字典(dictionary)，包含这张卡的ICCID, IMSI等所有数据：因为校验某一数据时，可能会需要其他数据作辅助
        '''
        raise ValidatorException("Un-implemented 'test()' in class '%s'" % self.__class__.__name__)

    def test(self, datas, logger):
        '''
            datas应为一个字典(dictionary)，包含这张卡的ICCID, IMSI等所有数据：因为校验某一数据时，可能会需要其他数据作辅助
            logger为上层检测循环的日记对象，支持 info(), debug(), warning(), error()等logging模块方法
        '''
        self.logger = logger
        try:
            self.dotest(datas)
        except ValidatorException:
            raise
        except Exception as e:
            raise ValidatorException("%s测试出现预料之外的异常，请检查测试脚本的语法、测试数据的格式等:\n%s" % (self.KEY, traceback.format_exc(e)))
        return True

    def getkv(self, datas):
        k = self.KEY
        v = datas.get(k, '').upper()
        return k, v

    def assertTrue(self, truestament, errormsg, truemsg=''):
        ''' 检测truestament是否为true，
            是则记录truemsg；
            否则记录truemsg并抛出异常，终止该校验器的检测
        '''
        if truestament:
            if truemsg:
                self.logger.info(truemsg)
            else:
                pass
        else:
            self.logger.error(errormsg)
            raise ValidatorException(errormsg)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)


class OrdernoValidator(Validator):

    LENGTH = 10
    KEY = 'ORDERNO'
    XH = 'XH'

    def dotest(self, datas):
        ''' 检查订单号值是否符合规范，例如XH20160102
        '''
        k, v = self.getkv(datas)
        if v:
            l = len(v)
            self.assertTrue(len(v)==self.LENGTH, '%s: %s 长度 %d 错误，应为 %d' % (k,v,l,self.LENGTH))
            self.assertTrue(v[:2]==self.XH, '%s: %s 前缀 %s 错误，应为%s' % (k,v,v[:2],self.XH))
            self.assertTrue(isalldigits(v[2:]), '%s: %s 值错误，%s之后应全部为0-9' % (k,v,self.XH))
        else:
            self.assertTrue(False, '%s不能为空' % k)


class ICCIDValidator(Validator):

    MII = '98'
    LENGTH = 20
    KEY = 'ICCID'

    def dotest(self, datas):
        ''' 检查ICCID值是否符合规范，例如982520506196020013F3
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06)，10.1.1	EF ICCID (ICC Identification)
                      ITU-T Rec. E.118 (05/2006) ，
        '''
        k, v = self.getkv(datas)
        if v:
            l = len(v)
            mii = v[:2]
            # TODO Country Code within ICCID should be extracted and shown
            self.assertTrue(len(v)==self.LENGTH, '%s: %s 长度 %d 错误，应为 %d' % (k,v,l,self.LENGTH))
            self.assertTrue(mii==self.MII, '%s: %s MII %s 错误，应为%s' % (k,v,mii,self.MII))
            self.assertTrue(isallhexdigits(v), '%s: %s 值错误，应全部为0-9a-fA-F' % (k,v))
            if 'F'==v[-2]:
                pan = api_util.swap(v)[:-1]
                self.assertTrue(api_util.verifyluhn(pan), '%s: %s Luhn校验位错误' % (k,v))
            else: # 某些老SIM卡的ICCID不是19位+‘F，没有luhn校验位
                self.warning(u'%s: %s 不符合ITU-T Rec. E.118规范，有可能是3GPP TS 11.11 V8.14.0中提及的旧格式。请联系数据中心确认。' % (k, v))
                self.assertTrue(isalldigits(v), '%s: %s 值错误，应全部为0-9' % (k,v))
        else:
            self.assertTrue(False, '%s不能为空' % k)


class IMSIValidator(Validator):

    LENGTH = 16
    KEY = 'IMSI'

    def dotest(self, datas):
        ''' 检查IMSI值是否符合规范，例如3943204046870774
            测试依据：3GPP TS 11.11 V8.14.0 (2007-06)，10.3.2	EF IMSI (IMSI)
                      3GPP TS 04.08: "Mobile radio interface layer 3 specification".
                      https://www.numberingplans.com/?page=plans&sub=imsinr
                      http://www.itu.int/rec/T-REC-E.123/en http://www.imei.info/operator-codes/
                      http://www.wrankl.de/SCH/SIM.pdf
        '''
        k, v = self.getkv(datas)
        if v:
            self.assertTrue(len(v)==self.LENGTH, '%s: %s 长度 %d 错误，应为 %d' % (k,v,len(v),self.LENGTH))
            self.assertTrue(isallhexdigits(v), '%s: %s 值错误，应全部为0-9a-fA-F' % (k,v))
            bits123 = int(v[:2], 16) &0x07
            parity = (int(v[:2], 16) &0x08) >>3 # TODO check parity
            mcc, mnc2, mnc3 = v[:3], v[3:5], v[3:6]
            # TODO Operator code consists of two parts: Mobile Network Code (MNC) and Mobile Country Code (MCC).
            # should be extracted and shown
            imsi_ascii = b2a( api_util.swap(v)[1:] )
            self.info('IMSI %s to IMSI_ASCII %s' % (v, imsi_ascii))
            self.assertTrue(bits123==1, '%s: %s 第1字节&0x07应为0x01' % (k,v))
        else:
            self.assertTrue(False, '%s不能为空' % k)


class IMSI_ASCIIValidator(Validator):

    LENGTH = 30
    KEY = 'IMSI_ASCII'

    def dotest(self, datas):
        ''' 检查IMSI的ASCII值是否符合规范，例如333334303230343634373837303531
        '''
        k, v = self.getkv(datas)
        if v:
            l = len(v)
            self.assertTrue(l==self.LENGTH, '%s: %s 长度 %d 错误，应为 %d' % (k,v,l,self.LENGTH))
            self.assertTrue(isallhexdigits(v), '%s: %s 值错误，应全部为0-9a-fA-F' % (k,v))
            imsi = datas.get(IMSIValidator.KEY, '')
            imsi_ascii = b2a( api_util.swap(imsi)[1:] )
            self.assertTrue(v==imsi_ascii, '%s: %s 不等于IMSI的ASCII格式 %s' % (k,v,imsi_ascii))
        else:
            self.assertTrue(False, '%s不能为空' % k)


class PINValidator(Validator):

    LENGTH = 16
    KEY = 'PIN'
    PAD = chr(0xFF)

    def dotest(self, datas):
        ''' 检查PIN值是否符合规范，例如 31313131FFFFFFFF
        '''
        k, v = self.getkv(datas)
        if v:
            l = len(v)
            self.assertTrue(l==self.LENGTH, '%s: %s 长度 %d 错误，应为 %d' % (k,v,l,self.LENGTH))
            self.assertTrue(isallhexdigits(v), '%s: %s 值错误，应全部为0-9a-fA-F' % (k,v))
            b, template = a2b(v), '0123456789'+self.PAD
            flag = all([c in template for c in b])
            self.assertTrue(flag, '%s: %s 值错误，应全部为30-39, FF' % (k,v))
            i = b.find(self.PAD)
            if i!=-1:
                PADs = b[i:]
                self.assertTrue(PADs.count(self.PAD)==len(PADs), '%s: %s 值错误，填充部分应全部为 FF' % (k,v))
        else:
            self.assertTrue(False, '%s不能为空' % k)

class PIN1Validator(PINValidator):

    LENGTH = 16
    KEY = 'PIN1'
    PAD = chr(0xFF)

class PIN2Validator(PINValidator):

    LENGTH = 16
    KEY = 'PIN2'
    PAD = chr(0xFF)


class PUKValidator(Validator):

    LENGTH = 16
    KEY = 'PUK'

    def dotest(self, datas):
        ''' 检查PUK值是否符合规范，例如 3139323430353331
        '''
        k, v = self.getkv(datas)
        if v:
            l = len(v)
            self.assertTrue(l==self.LENGTH, '%s: %s 长度 %d 错误，应为 %d' % (k,v,l,self.LENGTH))
            self.assertTrue(isalldigits(a2b(v)), '%s: %s 值错误，应全部为30-39' % (k,v))
        else:
            self.assertTrue(False, '%s不能为空' % k)

class PUK1Validator(PUKValidator):

    LENGTH = 16
    KEY = 'PUK1'

class PUK2Validator(PUKValidator):

    LENGTH = 16
    KEY = 'PUK2'


class ADMValidator(Validator):

    LENGTH = 16
    KEY = 'ADM'

    def dotest(self, datas):
        ''' 检查ADM值是否符合规范，例如 3639354432334339
        '''
        k, v = self.getkv(datas)
        if v:
            l = len(v)
            self.assertTrue(l==self.LENGTH, '%s: %s 长度 %d 错误，应为 %d' % (k,v,l,self.LENGTH))
            self.assertTrue(isallhexdigits(v), '%s: %s 值错误，应全部为0-9a-fA-F' % (k,v))
            b = a2b(v)
            template = string.ascii_letters + string.digits
            self.assertTrue(all([c in template for c in b]), "%s: %s 值错误，应全部为'0-9a-zA-Z'" % (k,v))
        else:
            self.assertTrue(False, '%s不能为空' % k)

class ADM1Validator(ADMValidator):

    LENGTH = 16
    KEY = 'ADM1'


class KIValidator(Validator):

    LENGTH = 32
    KEY = 'KI'

    def dotest(self, datas):
        ''' 检查KI值是否符合规范，例如 F16D7A3F018D7C96B7E603FB6C14ACC8
        '''
        k, v = self.getkv(datas)
        if v:
            l = len(v)
            self.assertTrue(l==self.LENGTH, '%s: %s 长度 %d 错误，应为 %d' % (k,v,l,self.LENGTH))
            self.assertTrue(isallhexdigits(v), '%s: %s 值错误，应全部为0-9a-fA-F' % (k,v))
            # TODO 检测弱KI
        else:
            self.assertTrue(False, '%s不能为空' % k)


class ACCValidator(Validator):

    LENGTH = 4
    KEY = 'ACC'

    def dotest(self, datas):
        ''' 检查ACC值是否符合规范，例如 0002
            3GPP TS 11.11 V8.14.0 (2007-06), 10.3.15	EF ACC (Access control class)
            http://www.forensicfocus.com/Forums/viewtopic/t=4565/
            https://en.wikipedia.org/wiki/ACCOLC
        '''
        k, v = self.getkv(datas)
        if v:
            l = len(v)
            self.assertTrue(l==self.LENGTH, '%s: %s 长度 %d 错误，应为 %d' % (k,v,l,self.LENGTH))
            self.assertTrue((int(v[:2], 16)&0x04)==0, '%s: %s 值错误，第1字节&0x04应当为0' % (k,v))
            # TODO 检查ACC与IMSI? ICCID?的关系
        else:
            self.assertTrue(False, '%s不能为空' % k)

class ACC1Validator(ACCValidator):

    LENGTH = 4
    KEY = 'ACC1'


class OPCValidator(Validator):

    LENGTH = 32
    KEY = 'OPC'

    def dotest(self, datas):
        ''' 检查OPC值是否符合规范，例如 CAB9BB7F4002B468F39CB9EFE79C62D2
            http://www.duoluodeyu.com/990.html
            3GPP TS 35.206 version 9.0.0 Release 9 12 ETSI TS 135 206 V9.0.0 (2010-02)
            https://www.secpulse.com/archives/39387.html
            http://diameter-protocol.blogspot.com/2013/06/usage-of-opopc-and-transport-key.html
        '''
        k, v = self.getkv(datas)
        if v:
            l = len(v)
            self.assertTrue(l==self.LENGTH, '%s: %s 长度 %d 错误，应为 %d' % (k,v,l,self.LENGTH))
            self.assertTrue(isallhexdigits(v), '%s: %s 值错误，应全部为0-9a-fA-F' % (k,v))
            # TODO 检查OPC与KI的关系
            # TODO 检测weak OPC
        else:
            self.assertTrue(False, '%s不能为空' % k)

class KIC1Validator(OPCValidator):

    LENGTH = 32
    KEY = 'KIC1'

class KID1Validator(OPCValidator):

    LENGTH = 32
    KEY = 'KID1'

class KID1Validator(OPCValidator):

    LENGTH = 32
    KEY = 'KID1'

class KIK1Validator(OPCValidator):

    LENGTH = 32
    KEY = 'KIK1'

class SYSPINValidator(OPCValidator):

    LENGTH = 16
    KEY = 'SYSPIN'

class PRINT_ICCIDValidator(Validator):

    #LENGTH = 20
    KEY = 'PRINT_ICCID'

    def dotest(self, datas):
        ''' 检查ICCID的PRINT值是否符合规范，例如8952020516692000313F
        '''
        k, v = self.getkv(datas)
        if v:
            self.assertTrue(isallhexdigits(v), '%s: %s 值错误，应全部为0-9a-fA-F' % (k,v))
            iccid = datas.get(ICCIDValidator.KEY, '')
            self.assertTrue(api_util.swap(v)==iccid, '%s: %s 不等于ICCID的高低位交换 %s' % (k,v,iccid))
        else:
            self.assertTrue(False, '%s不能为空' % k)


class PRINT_PIN1Validator(Validator):

    #LENGTH = 16
    KEY = 'PRINT_PIN1'

    def dotest(self, datas):
        ''' 检查PIN1的打印值是否符合规范，例如 1111
        '''
        k, v = self.getkv(datas)
        if v:
            l = len(v)
            self.assertTrue(l>=4 and l<=8, '%s: %s 长度 %d 错误，应为4至8' % (k,v,l))
            self.assertTrue(isalldigits(v), '%s: %s 值错误，应全部为0-9' % (k,v))
            pin1 = datas.get(PIN1Validator.KEY, '')
            v1 = (b2a(v) + 'F'*16)[:PIN1Validator.LENGTH] # 将打印值转换为十六进制的PIN1值
            self.assertTrue(v1==pin1, '%s: %s 打印值不等于PIN1: %s 值' % (k,v,pin1))
        else:
            self.assertTrue(False, '%s不能为空' % k)

class PRINT_PUK1Validator(Validator):

    LENGTH = 8
    KEY = 'PRINT_PUK1'

    def dotest(self, datas):
        ''' 检查PUK1的打印值是否符合规范，例如 19240531
        '''
        k, v = self.getkv(datas)
        if v:
            l = len(v)
            self.assertTrue(l==self.LENGTH, '%s: %s 长度 %d 错误，应等于 %d' % (k,v,l,self.LENGTH))
            self.assertTrue(isalldigits(v), '%s: %s 值错误，应全部为0-9' % (k,v))
            puk1 = datas.get(PUK1Validator.KEY, '')
            v1 = b2a(v) # 将打印值转换为十六进制的PUK1值
            self.assertTrue(v1==puk1, '%s: %s 打印值不等于PUK1: %s 值' % (k,v,puk1))
        else:
            self.assertTrue(False, '%s不能为空' % k)

#-------------------------------------------------------------------------------
DefaultValidators = {
        'SIM' : {
                    'ICCID': ICCIDValidator(),
                    'IMSI': IMSIValidator(),
                    'IMSI_ASCII': IMSI_ASCIIValidator(),
                    'PIN1': PIN1Validator(),
                    'PIN2': PIN2Validator(),
                    'PUK1': PUK1Validator(),
                    'PUK2': PUK2Validator(),
                    'ADM1': ADM1Validator(),
                    'KI': KIValidator(),
                    'ACC1': ACC1Validator(),
                    'OPC': OPCValidator(),
                    'KIC1': KIC1Validator(),
                    'KID1': KID1Validator(),
                    'KIK1': KIK1Validator(),
                    'SYSPIN': SYSPINValidator(),
                    'PRINT_ICCID': PRINT_ICCIDValidator(),
                    'PRINT_PIN1': PRINT_PIN1Validator(),
                    'PRINT_PUK1': PRINT_PUK1Validator(),
                },
        'BANK': dict(),
        }


def getdefault(name='SIM'):
    return DefaultValidators.get(name, dict())


#-------------------------------------------------------------------------------
class TestModule(unittest.TestCase):
    ''' api_validators模块的单元测试 '''

    @classmethod
    def setUpClass(cls):
        cls.logger = logging.getLogger()

    def test_isallhexdigits(self):
        self.assertTrue(isallhexdigits(''))
        for c in string.hexdigits:
            self.assertTrue(isallhexdigits(c))
        set1 = sets.Set(map(chr, range(0,0x100)))
        set2 = sets.Set(string.hexdigits)
        set3 = set1 - set2
        s2 = ''.join(set2)
        s3 = ''.join(set3)
        for c in s3:
            self.assertTrue(not isallhexdigits(c))
            self.assertTrue(not isallhexdigits(s2+c))

    def test_isalldigits(self):
        self.assertTrue(isalldigits(''))
        for c in string.digits:
            self.assertTrue(isalldigits(c))
        set1 = sets.Set(map(chr, range(0,0x100)))
        set2 = sets.Set(string.digits)
        set3 = set1 - set2
        s2 = ''.join(set2)
        s3 = ''.join(set3)
        for c in s3:
            self.assertTrue(not isalldigits(c))
            self.assertTrue(not isalldigits(s2+c))

    def test_Validator(self):
        val = Validator()
        dit = {'KEY':'VALUE'}
        self.assertRaises(ValidatorException, val.test, dit, self.logger)
        k, v = val.getkv(dit)
        self.assertTrue(k=='KEY' and v=='VALUE')

    def test_ICCIDValidator(self):
        v = ICCIDValidator()
        self.assertTrue(v.test({'ICCID':  '982520506196020013F3'}, self.logger))
        self.assertTrue(v.test({'ICCID':  '98252050619602001393'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'ICCID':  '982520506196020013E3'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ICCID': '892520506196020013F3'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ICCID': '982520506196020013F4'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ICCID': '98FF20506196020013F3F'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ICCID': '98FF20506196020013F3FF'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ICCID': '982520506196020013E3'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ICCID': '982520506196020013A3'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ICCID': '982520506196020013Fo'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ICCID': ''}, self.logger)

    def test_IMSIValidator(self):
        v = IMSIValidator()
        self.assertTrue(v.test({'IMSI':  '3943204046870774'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'IMSI': '39432040468707749'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'IMSI': '3A43204046870774'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'IMSI': 'JA43204046870774'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'IMSI': ''}, self.logger)

    def test_IMSI_ASCIIValidator(self):
        v = IMSI_ASCIIValidator()
        self.assertTrue(v.test({'IMSI':  '3943204046870774', 'IMSI_ASCII':'333334303230343634373837303437'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'IMSI': '3943204046870774', 'IMSI_ASCII':'44333334303230343634373837303437'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'IMSI': '3943204046870774', 'IMSI_ASCII':'F33334303230343634373837303437'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'IMSI_ASCII':''}, self.logger)

    def test_PIN1Validator(self):
        v = PIN1Validator()
        self.assertTrue(v.test({'PIN1':  '31313131FFFFFFFF'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'PIN1': '3131313131FFFFFFFF'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PIN1': 'o1313131FFFFFFFF'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PIN1': '41313131FFFFFFFF'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PIN1': '31313131FEFFFFFF'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PIN1': '3A313131FFFFFFFF'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PIN1': '31313131FFFFFFF0'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PIN1': ''}, self.logger)

    def test_PIN2Validator(self):
        v = PIN2Validator()
        self.assertTrue(v.test({'PIN2':  '31313131FFFFFFFF'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'PIN2': '3131313131FFFFFFFF'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PIN2': 'o1313131FFFFFFFF'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PIN2': '41313131FFFFFFFF'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PIN2': '31313131FEFFFFFF'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PIN2': '3A313131FFFFFFFF'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PIN2': '31313131FFFFFFF0'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PIN2': ''}, self.logger)

    def test_PUK1Validator(self):
        v = PUK1Validator()
        self.assertTrue(v.test({'PUK1':  '3139323430353331'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'PUK1': '3139323430353331F'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PUK1': '39323430353331F'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PUK1': '4139323430353331'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PUK1': ''}, self.logger)

    def test_PUK2Validator(self):
        v = PUK2Validator()
        self.assertTrue(v.test({'PUK2':  '3139323430353331'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'PUK2': '3139323430353331F'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PUK2': '39323430353331F'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PUK2': '4139323430353331'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PUK2': ''}, self.logger)

    def test_ADM1Validator(self):
        v = ADM1Validator()
        self.assertTrue(v.test({'ADM1':  '3639354432334339'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'ADM1': '36393544323343'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ADM1': '363935443233433939'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ADM1': 'o639354432334339'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ADM1': 'F639354432334339'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ADM1': 'FE39354432334339'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ADM1': ''}, self.logger)

    def test_KIValidator(self):
        v = KIValidator()
        self.assertTrue(v.test({'KI':  'F16D7A3F018D7C96B7E603FB6C14ACC8'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'KI': '16D7A3F018D7C96B7E603FB6C14ACC8'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'KI': 'F16D7A3F018D7C96B7E603FB6C14ACC8C8'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'KI': ' 16D7A3F018D7C96B7E603FB6C14ACC8'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'KI': ''}, self.logger)

    def test_ACC1Validator(self):
        v = ACC1Validator()
        self.assertTrue(v.test({'ACC1':  '0002'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'ACC1': '002'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ACC1': '00022'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ACC1': '0402'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ACC1': ''}, self.logger)

    def test_OPCValidator(self):
        v = OPCValidator()
        self.assertTrue(v.test({'OPC':  'CAB9BB7F4002B468F39CB9EFE79C62D2'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'OPC': 'B9BB7F4002B468F39CB9EFE79C62D2'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'OPC': 'CAB9BB7F4002B468F39CB9EFE79C62D2D2'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'OPC': ' AB9BB7F4002B468F39CB9EFE79C62D2'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'OPC': ''}, self.logger)

    def test_KIC1Validator(self):
        v = KIC1Validator()
        self.assertTrue(v.test({'KIC1':  'CAB9BB7F4002B468F39CB9EFE79C62D2'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'KIC1': 'B9BB7F4002B468F39CB9EFE79C62D2'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'KIC1': 'CAB9BB7F4002B468F39CB9EFE79C62D2D2'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'KIC1': ' AB9BB7F4002B468F39CB9EFE79C62D2'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'KIC1': ''}, self.logger)

    def test_KID1Validator(self):
        v = KID1Validator()
        self.assertTrue(v.test({'KID1':  'CAB9BB7F4002B468F39CB9EFE79C62D2'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'KID1': 'B9BB7F4002B468F39CB9EFE79C62D2'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'KID1': 'CAB9BB7F4002B468F39CB9EFE79C62D2D2'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'KID1': ' AB9BB7F4002B468F39CB9EFE79C62D2'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'KID1': ''}, self.logger)

    def test_KIK1Validator(self):
        v = KIK1Validator()
        self.assertTrue(v.test({'KIK1':  'CAB9BB7F4002B468F39CB9EFE79C62D2'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'KIK1': 'B9BB7F4002B468F39CB9EFE79C62D2'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'KIK1': 'CAB9BB7F4002B468F39CB9EFE79C62D2D2'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'KIK1': ' AB9BB7F4002B468F39CB9EFE79C62D2'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'KIK1': ''}, self.logger)

    def test_SYSPINValidator(self):
        v = SYSPINValidator()
        self.assertTrue(v.test({'SYSPIN':  'F39CB9EFE79C62D2'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'SYSPIN': '9CB9EFE79C62D2'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'SYSPIN': 'F39CB9EFE79C62D2D2'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'SYSPIN': ' 39CB9EFE79C62D2'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'SYSPIN': ''}, self.logger)

    def test_PRINT_ICCIDValidator(self):
        v = PRINT_ICCIDValidator()
        self.assertTrue(v.test({'ICCID':  '982520506196020013F3', 'PRINT_ICCID':'8952020516692000313F'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'ICCID': '982520506196020013F3', 'PRINT_ICCID':' 952020516692000313F'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'ICCID': '982520506196020013F4', 'PRINT_ICCID':'8952020516692000313F'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PRINT_ICCID':''}, self.logger)

    def test_PRINT_PIN1Validator(self):
        v = PRINT_PIN1Validator()
        self.assertTrue(v.test({'PIN1':  '31313131FFFFFFFF', 'PRINT_PIN1':'1111'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'PIN1': '31313131FFFFFFFF', 'PRINT_PIN1':'111'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PIN1': '31313131FFFFFFFF', 'PRINT_PIN1':'111111111'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PIN1': '31313131FFFFFFFF', 'PRINT_PIN1':'z111'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PIN1': '31313131FFFFFFFF', 'PRINT_PIN1':'2111'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PRINT_PIN1':''}, self.logger)

    def test_PRINT_PUK1Validator(self):
        v = PRINT_PUK1Validator()
        self.assertTrue(v.test({'PUK1':  '3139323430353331', 'PRINT_PUK1':'19240531'}, self.logger))
        self.assertRaises(ValidatorException, v.test, {'PUK1': '3139323430353331', 'PRINT_PUK1':'9240531'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PUK1': '3139323430353331', 'PRINT_PUK1':'192405311'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PUK1': '3139323430353331', 'PRINT_PUK1':' 9240531'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PUK1': '3139323430353331', 'PRINT_PUK1':'29240531'}, self.logger)
        self.assertRaises(ValidatorException, v.test, {'PRINT_PUK1':''}, self.logger)

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    unittest.main()

