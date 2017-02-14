#!/usr/env python
# -*- coding: utf-8 -*-

"""
    该模块提供一个用于比对卡内数据和输入数据的python类
    This module implements a python class to check if data within COS mathches Input Data provided by data center.


    __author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
    __date__ = "Aug 2016"
    __version__ = "0.1.0"

    Copyright 2016 XH Smart Card Co,. Ltd

    Author: wg@china-xinghan.com
"""
import logging, os, string, collections, unittest, traceback

import api_inputdata
import api_validators
import api_util
import api_tlv
import api_pcsc


#----------------------------------------------------------------------------
u = api_util.u
a2b = api_util.a2b
b2a = api_util.b2a

SW_NO_ERROR = '9000'
SW_FILE_NOT_FOUND = '6A82'
SW_FILE_NOT_FOUND_2G = '9404' # SIM卡的'文件未找到' SW是9404，不是6A82
SW_PIN1_DISABLED = '6984'

FID = {
    'MF' : '3F00',
    'EF_DIR' : '2F00',
    'EF_ICCID' : '2FE2',
    'DF_GSM' : '7F20',
    'DF_DCS1800' : '7F21',
    'EF_IMSI' : '6F07',
    'EF_ACC1' : '6F78',
}

unpacktlv = api_tlv.unpacktlv
unpacktlvs = api_tlv.unpacktlvs
unpacktlvs2dict = api_tlv.unpacktlvs2dict

ValidatorException = api_validators.ValidatorException

#----------------------------------------------------------------------------
class ApplicationTemplate(object):
    ''' 一个模拟USIM EF_DIR的记录内容的类，可以分析、保存application（如USIM、ISIM）的AID、Label
    '''

    def __init__(self, tlv):
        ''' 
            ETSI TS 102 221 V12.0.0 (2014-12)
            13.1 EFDIR
            Table 13.2: Coding of an application template entry

            tlv: 61184F10A0000000871002FF86FF0289060100FF50045553494D 
        '''
        t, l, v = unpacktlv(tlv)
        assert t=='61'
        length = int(l, 16)
        assert length>=3 and length<=127
        dit = unpacktlvs2dict(v)
        self.aid = dit['4F'][2]
        self.label = dit['50'][2]

#----------------------------------------------------------------------------
class FileControlInformation(object):
    ''' 一个模拟USIM EF的FCI响应信息的类，可通过该类的实例存储、解析文件的FCI信息
    '''

    def __init__(self, tlv):
        ''' ISO/IEC 7816-4:2005(E)
            5.3.3 File control information

            ETSI TS 102 221 V12.0.0 (2014-12)
            11.1.1.3 Response Data
            11.1.1.3.2 Response for an EF

            tlv: 62268205422100260283022F00A50AC00100CD02FF00CA01848A01058B032F06018002004C8801F0
        '''
        t, l, v = unpacktlv(tlv)
        assert t=='62'
        dit = unpacktlvs2dict(v)
        self.parsefiledescriptor(dit['82'])
        self.parsefileidentifier(dit['83'])
        self.parsefilesize(dit['80'])
        for x in ('8B', '8C', 'AB'):
            if x in dit:
                self.parsesecureattribute(dit[x])
                break

    def parsefiledescriptor(self, tlv):
        ''' 11.1.1.4.3 File Descriptor

            82 05 4221002602
        '''
        t, l, v = tlv
        assert l=='02' or l=='05'
        fdb = int(v[:2], 16)
        self.isshareable = True if (fdb&0xC0)==0x40 else False
        self.isworkingef = True if (fdb&0xB8)==0x00 else False
        self.isinternalef = True if (fdb&0xB8)==0x08 else False
        self.isdf = True if (fdb&0xB8)==0x38 else False
        self.isadf = True if (fdb&0xB8)==0x38 else False
        self.istransparent = True if (fdb&0x87)==0x01 else False
        self.islinearfixed = True if (fdb&0x87)==0x02 else False
        self.iscyclic = True if (fdb&0x87)==0x06 else False
        self.isbertlv = True if (fdb&0xBF)==0x39 else False

        if self.islinearfixed or self.iscyclic:
            if l=='05':
                self.recordlength = int(v[4:8], 16)
                self.numberofrecords = int(v[8:], 16)

    def parsefileidentifier(self, tlv):
        ''' 11.1.1.4.4 File identifier
        '''
        t, l, v = tlv
        assert l=='02'
        self.fileid = v

    def parsefilesize(self, tlv):
        ''' 11.1.1.4.1 File size
        '''
        t, l, v = tlv
        assert len(v) >= 2
        self.filesize = int(v, 16)

    def parsesecureattribute(self, tlv):
        ''' 11.1.1.4.7 Security attributes
            11.1.1.4.7.3 Referenced to expanded format
        '''
        t, l, v = tlv
        assert len(v) == 6
        self.arrfileid = v[:4]
        self.arrrecordnumber = int(v[4:], 16)


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

    def verifypin(self, pin, index=1, expectSW=SW_NO_ERROR):
        ''' 
        '''
        length = len(pin)/2
        apdu = '002000%.2X%.2X%s' % (index&0xFF, length, pin)
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
class Validator(object):

    KEY = 'KEY'

    def __init__(self):
        pass

    def dotest(self, datas, card):
        ''' 子类应当覆盖该方法，实现对value = datas[KEY]的校验
            datas: 应为一个字典(dictionary)，包含这张卡的ICCID, IMSI等所有数据：因为校验某一数据时，可能会需要其他数据作辅助
            card:  一个可以操作USIM卡的对象
        '''
        raise ValidatorException("Un-implemented 'test()' in class '%s'" % self.__class__.__name__)

    def test(self, datas, logger, card):
        '''
            datas应为一个字典(dictionary)，包含这张卡的ICCID, IMSI等所有数据：因为校验某一数据时，可能会需要其他数据作辅助
            logger为上层检测循环的日记对象，支持 info(), debug(), warning(), error()等logging模块方法
            card为上层检测循环提供的日记对象，支持reset, select, readbinary等方法
        '''
        self.logger = logger
        try:
            self.dotest(datas, card)
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


#----------------------------------------------------------------------------
class EmptyValidator(Validator):

    KEY = 'EMPTY'

    def dotest(self, datas, card):
        k, v = self.getkv(datas)
        self.warning('输入数据%s尚未检查' % k)

class ATRValidator(Validator):

    KEY = 'ATR'

    def dotest(self, datas, card):
        ''' 检查卡ATR值是否与输入数据相等
        '''
        k, v = self.getkv(datas)
        if v:
            atr = card.reset()
            self.assertTrue(v==atr, '%s : %s 不等于卡内值 %s' % (k,v,atr))
        else:
            self.assertTrue(False, '输入数据中%s不能为空' % k)

class ICCIDValidator(Validator):

    KEY = 'ICCID'

    def dotest(self, datas, card):
        ''' 检查卡内ICCID值与输入数据相等，例如982520506196020013F3
        '''
        k, v = self.getkv(datas)
        if v:
            card.reset()
            card.select(FID['MF'])
            card.select(FID['EF_ICCID'])
            iccid, sw = card.readbinary(0, len(v)/2)
            self.assertTrue(v==iccid, '%s : %s 不等于卡内值 %s' % (k,v,iccid))
        else:
            self.assertTrue(False, '输入数据中%s不能为空' % k)


class IMSIValidator(Validator):

    KEY = 'IMSI'

    def dotest(self, datas, card):
        ''' 检查卡内IMSI值与输入数据相等，例如083943204035762283
        '''
        k, v = self.getkv(datas)
        if v:
            #1 USIM/6F07
            card.reset()
            aid = card.getusimaid()
            card.selectbyaid(aid)
            r, sw = card.select(FID['EF_IMSI'])
            fci = FileControlInformation(r)
            imsi, sw = card.readbinary(0, fci.filesize)
            self.assertTrue('08'+v==imsi, "%s : '08'+%s 不等于卡内值 %s" % (k,v,imsi))

            #2 3F00/7F20/6F07
            card.reset()
            card.select(FID['MF'])
            card.select(FID['DF_GSM'])
            r, sw = card.select(FID['EF_IMSI'], expectSW='')
            if sw==SW_NO_ERROR:
                fci = FileControlInformation(r)
                imsi, sw = card.readbinary(0, fci.filesize)
                self.assertTrue('08'+v==imsi, "%s : '08'+%s 不等于卡内值 %s" % (k,v,imsi))
            elif sw==SW_FILE_NOT_FOUND:
                self.warning('%s : DF_GSM EF_IMSI不存在！请确认是否不需要支持USIM的2G模式' % k)
            else:
                self.error('%s : %s 选择DF_GSM EF_IMSI状态字异常！'%(k,sw))

            #3 3F00/7F21/6F07
            r, sw = card.select(FID['DF_DCS1800'], expectSW='')
            if sw==SW_NO_ERROR:
                r, sw = card.select(FID['EF_IMSI'], expectSW='')
                if sw==SW_NO_ERROR:
                    fci = FileControlInformation(r)
                    imsi, sw = card.readbinary(0, fci.filesize)
                    self.assertTrue('08'+v==imsi, "%s : '08'+%s 不等于卡内值 %s" % (k,v,imsi))
                elif sw==SW_FILE_NOT_FOUND:
                    self.warning('%s : DF_DCS1800 EF_IMSI不存在！请确认是否不需要支持USIM的2G模式' % k)
                else:
                    self.error('%s : %s 选择DF_DCS1800 EF_IMSI状态字异常！'%(k,sw))
            elif sw==SW_FILE_NOT_FOUND:
                self.warning('%s : DF_DCS1800不存在！请确认是否不需要支持USIM的2G模式' % k)
            else:
                self.error('%s : %s 选择DF_DCS1800状态字异常！'%(k,sw))
        else:
            self.assertTrue(False, '输入数据中%s不能为空' % k)

class IMSIValidator_SIM(Validator):
    ''' 2G SIM卡的IMSI校验器
    '''
    KEY = 'IMSI'

    def dotest(self, datas, card):
        ''' 检查卡内IMSI值与输入数据相等，例如083943204035762283
        '''
        k, v = self.getkv(datas)
        if v:
            #1 USIM/6F07 # SIM卡没有USIM ADF
            # card.reset()
            # aid = card.getusimaid()
            # card.selectbyaid(aid)
            # r, sw = card.select(FID['EF_IMSI'])
            # fci = FileControlInformation(r)
            # imsi = card.readbinary(0, fci.filesize)
            # self.assertTrue('08'+v==imsi, "%s : '08'+%s 不等于卡内值 %s" % (k,v,imsi))

            #2 3F00/7F20/6F07
            card.reset()
            card.select(FID['MF'])
            card.select(FID['DF_GSM'])
            r, sw = card.select(FID['EF_IMSI'], expectSW='')
            if sw==SW_NO_ERROR:
                fci = FileControlInformation(r)
                imsi, sw = card.readbinary(0, fci.filesize)
                self.assertTrue('08'+v==imsi, "%s : '08'+%s 不等于卡内值 %s" % (k,v,imsi))
            elif sw==SW_FILE_NOT_FOUND_2G:
                self.warning('%s : DF_GSM EF_IMSI不存在！请确认是否不需要支持2G SIM模式' % k)
            else:
                self.error('%s : %s 选择DF_GSM EF_IMSI状态字异常！'%(k,sw))

            #3 3F00/7F21/6F07
            card.select(FID['DF_DCS1800'])
            r, sw = card.select(FID['EF_IMSI'], expectSW='')
            if sw==SW_NO_ERROR:
                fci = FileControlInformation(r)
                imsi, sw = card.readbinary(0, fci.filesize)
                self.assertTrue('08'+v==imsi, "%s : '08'+%s 不等于卡内值 %s" % (k,v,imsi))
            elif sw==SW_FILE_NOT_FOUND_2G:
                self.warning('%s : DF_DCS1800 EF_IMSI不存在！请确认是否不需要支持2G SIM模式' % k)
            else:
                self.error('%s : %s 选择DF_DCS1800 EF_IMSI状态字异常！'%(k,sw))
        else:
            self.assertTrue(False, '输入数据中%s不能为空' % k)

class PIN1Validator(EmptyValidator):
    KEY = 'PIN1'

    def dotest(self, datas, card):
        ''' 检查卡内PIN1值与输入数据相等，例如31313131FFFFFFFF
        '''
        k, v = self.getkv(datas)
        if v:
            r, sw = card.verifypin(v, expectSW='')
            if sw==SW_NO_ERROR:
                pass
            elif sw==SW_PIN1_DISABLED:
                card.enablepin(v) # 尝试激活PIN1
                card.disablepin(v) # 将PIN1为失效状态
            else:
                self.error('%s : %s 校验PIN1时状态字异常！'%(k,sw))
        else:
            self.assertTrue(False, '输入数据中%s不能为空' % k)

class PUK1Validator(EmptyValidator):
    KEY = 'PUK1'

class PIN2Validator(EmptyValidator):
    KEY = 'PIN2'

class PUK2Validator(EmptyValidator):
    KEY = 'PUK2'

class ADM1Validator(EmptyValidator):
    KEY = 'ADM1'

class KIValidator(EmptyValidator):
    KEY = 'KI'

class ACC1Validator(EmptyValidator):

    KEY = 'ACC1'

    def dotest(self, datas, card):
        ''' 检查ACC值是否符合输入数据，例如 0002

            3GPP TS 31.102 version 13.3.0 Release 13 32 ETSI TS 131 102 V13.3.0 (2016-04)
            4.2.15 EFACC (Access Control Class)

            3GPP TS 51.011 V4.15.0 (2005-06) Release 4
            10.3.15	EFACC (Access control class)
        '''
        k, v = self.getkv(datas)
        if v:
            #1 USIM/EF_ACC1
            card.reset()
            aid = card.getusimaid()
            card.selectbyaid(aid)
            r, sw = card.select(FID['EF_ACC1'])
            fci = FileControlInformation(r)
            v1, sw = card.readbinary(0, fci.filesize)
            self.assertTrue(v==v1, "%s : %s 不等于卡内值 %s" % (k,v,v1))

            card.reset()
            card.select(FID['MF'])
            card.select(FID['DF_GSM'])
            r, sw = card.select(FID['EF_ACC1'], expectSW='')
            if sw==SW_NO_ERROR:
                fci = FileControlInformation(r)
                v1, sw = card.readbinary(0, fci.filesize)
                self.assertTrue(v==v1, "%s : %s 不等于卡内值 %s" % (k,v,v1))
            else:
                self.warning('%s : DF_GSM EF_ACC1不存在！请确认是否不需要支持USIM的2G模式' % k)
        else:
            self.assertTrue(False, '输入数据中%s不能为空' % k)

class OPCValidator(EmptyValidator):
    KEY = 'OPC'

class IMSI_ASCIIValidator(Validator):

    KEY = 'IMSI_ASCII'

    def dotest(self, datas, card):
        ''' 检查卡内IMSI值是否与输入数据相等
        '''
        k, v = self.getkv(datas)
        if v:
            imsi = api_util.swap(a2b('39'+v))

            #1 USIM/6F07
            card.reset()
            aid = card.getusimaid()
            card.selectbyaid(aid)
            r, sw = card.select(FID['EF_IMSI'])
            fci = FileControlInformation(r)
            imsi1, sw = card.readbinary(0, fci.filesize)
            self.assertTrue('08'+imsi==imsi1, "%s : '08'+%s 不等于卡内值 %s" % (k,imsi,imsi1))

            #2 3F00/7F20/6F07
            card.reset()
            card.select(FID['MF'])
            card.select(FID['DF_GSM'])
            r, sw = card.select(FID['EF_IMSI'], expectSW='')
            if sw==SW_NO_ERROR:
                fci = FileControlInformation(r)
                imsi1, sw = card.readbinary(0, fci.filesize)
                self.assertTrue('08'+imsi==imsi1, "%s : '08'+%s 不等于卡内值 %s" % (k,imsi,imsi1))
            elif sw==SW_FILE_NOT_FOUND:
                self.warning('%s : DF_GSM EF_IMSI不存在！请确认是否不需要支持USIM的2G模式' % k)
            else:
                self.error('%s : %s 选择DF_GSM EF_IMSI状态字异常！'%(k,sw))

            #3 3F00/7F21/6F07
            r, sw = card.select(FID['DF_DCS1800'], expectSW='')
            if sw==SW_NO_ERROR:
                r, sw = card.select(FID['EF_IMSI'], expectSW='')
                if sw==SW_NO_ERROR:
                    fci = FileControlInformation(r)
                    imsi, sw = card.readbinary(0, fci.filesize)
                    self.assertTrue('08'+imsi==imsi1, "%s : '08'+%s 不等于卡内值 %s" % (k,imsi,imsi1))
                elif sw==SW_FILE_NOT_FOUND:
                    self.warning('%s : DF_DCS1800 EF_IMSI不存在！请确认是否不需要支持USIM的2G模式' % k)
                else:
                    self.error('%s : %s 选择DF_DCS1800 EF_IMSI状态字异常！'%(k,sw))
            elif sw==SW_FILE_NOT_FOUND:
                self.warning('%s : DF_DCS1800不存在！请确认是否不需要支持USIM的2G模式' % k)
            else:
                self.error('%s : %s 选择DF_DCS1800状态字异常！'%(k,sw))
        else:
            self.assertTrue(False, '输入数据中%s不能为空' % k)

class KIC1Validator(EmptyValidator):
    KEY = 'KIC1'

class KID1Validator(EmptyValidator):
    KEY = 'KID1'

class KIK1Validator(EmptyValidator):
    KEY = 'KIK1'

class SYSPINValidator(EmptyValidator):
    KEY = 'SYSPIN'

class PRINT_ICCIDValidator(EmptyValidator):
    KEY = 'PRINT_ICCID'

class PRINT_PIN1Validator(EmptyValidator):
    KEY = 'PRINT_PIN1'

class PRINT_PUK1Validator(EmptyValidator):
    KEY = 'PRINT_PUK1'

#----------------------------------------------------------------------------
DefaultValidators = {
        'USIM' : {
            'ATR' : ATRValidator(),
            'ICCID' : ICCIDValidator(),
            'IMSI' : IMSIValidator(),
            'PIN1' : PIN1Validator(),
            'PUK1' : PUK1Validator(),
            'PIN2' : PIN2Validator(),
            'PUK2' : PUK2Validator(),
            'ADM1' : ADM1Validator(),
            'KI' : KIValidator(),
            'ACC1' : ACC1Validator(),
            'OPC' : OPCValidator(),
            'IMSI_ASCII' : IMSI_ASCIIValidator(),
            'KIC1' : KIC1Validator(),
            'KID1' : KID1Validator(),
            'KIK1' : KIK1Validator(),
            'SYSPIN' : SYSPINValidator(),
            'PRINT_ICCID' : PRINT_ICCIDValidator(),
            'PRINT_PIN1' : PRINT_PIN1Validator(),
            'PRINT_PUK1' : PRINT_PUK1Validator(),
            },
        'SIM' : {
            'ICCID' : ICCIDValidator(),
            },
        }


#----------------------------------------------------------------------------
class UsimDataValidator(object):
    ''' 该类将'数据'和'卡'，传递给'校验器'，实现了卡内数据和输入数据（即个性化数据）的比对功能
        校验器将通过'卡'访问手机卡，完成某一项数据的校验。校验的过程中，调用该类实现的logger相关方法，记录校验信息。
    '''

    def __init__(self, usim=Usim(), default_validators=DefaultValidators.get('USIM')):
        '''
            usim : USIM或SIM类的对象实例，用于操作卡
            default_validators  :   default validators
        '''
        # check correctness of all parameters
        # logging if any problem found
        self.usim = usim
        self.default_validators = default_validators
        self.logger = logging.getLogger(self.__class__.__name__)
        self.clearno()

    def clearno(self):
        self.passedno, self.warningno, self.errorno = 0, 0, 0

    def dotest(self, datas, validators=None):
        ''' 
            校验时，先在用户提供的validators中查找符合keyword的validator，没找到则在默认validators中查找

            validators : A dictionary of validators, for special/unusual keywords.
        '''
        for k, v in datas.items():
            if validators:
                validator = validators[k] if k in validators else self.default_validators.get(k, None)
            else:
                validator = self.default_validators.get(k, None)
            if validator:
                try:
                    self.assertTrue(validator.test(datas, self, self.usim), '%s: %s 校验不通过' % (k,v), '%s: %s 校验通过' % (k,v))
                except api_validators.ValidatorException as e:
                    self.error('%s: %s 校验不通过，出现异常:\n%s' % (k,v,str(e)))
            else:
                self.warning('未找到 %s 的校验器，无法校验该项数据 %s' % (k,v))

    def test(self, datas, validators=dict()):
        self.start()
        self.dotest(datas, validators)
        return self.end()

    def start(self):
        self.clearno()

    def end(self):
        return self.passedno, self.warningno, self.errorno

    def assertTrue(self, truestament, errormsg, truemsg=''):
        if truestament:
            if truemsg:
                self.passed(truemsg)
            else:
                pass
        else:
            self.error(errormsg)
        return truestament

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(u(msg), *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(u(msg), *args, **kwargs)

    def passed(self, msg, *args, **kwargs):
        self.passedno += 1
        self.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.warningno += 1
        self.logger.warning(u(msg), *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.errorno += 1
        self.logger.error(u(msg), *args, **kwargs)


#-------------------------------------------------------------------------------
class TestModule(unittest.TestCase):
    ''' 本模块的单元测试 '''

    @classmethod
    def setUpClass(cls):
        cls.logger = logging.getLogger()
        cls.usim = Usim()

    def test_ApplicationTemplate(self):
        tlv = '61184F10A0000000871002FF86FF0289060100FF50045553494D' 
        at = ApplicationTemplate(tlv)
        self.assertTrue(at.aid=='A0000000871002FF86FF0289060100FF')
        self.assertTrue(at.label=='5553494D')

    def test_FileControlInformation(self):
        tlv = "62268205422100260283022F00A50AC00100CD02FF00CA01848A01058B032F06018002004C8801F0"
        fci = FileControlInformation(tlv)
        self.assertTrue(fci.isshareable==True)
        self.assertTrue(fci.isworkingef==True)
        self.assertTrue(fci.isinternalef==False)
        self.assertTrue(fci.isdf==False)
        self.assertTrue(fci.isadf==False)
        self.assertTrue(fci.istransparent==False)
        self.assertTrue(fci.islinearfixed==True)
        self.assertTrue(fci.iscyclic==False)
        self.assertTrue(fci.isbertlv==False)
        self.assertTrue(fci.recordlength==38)
        self.assertTrue(fci.numberofrecords==2)
        self.assertTrue(fci.fileid=='2F00')
        self.assertTrue(fci.filesize==76)
        self.assertTrue(fci.arrfileid=='2F06')
        self.assertTrue(fci.arrrecordnumber==1)

    def test_reset(self):
        self.assertTrue(self.usim.reset()!='')

    def test_verifypin(self):
        usim = self.usim
        usim.reset()
        pin1 = '31313131FFFFFFFF'
        r, sw = usim.verifypin(pin1, expectSW='')
        if sw==SW_NO_ERROR:
            self.assertTrue(r=='')
        elif sw==SW_PIN1_DISABLED:
            usim.enablepin(pin1)
            usim.disablepin(pin1)
        else:
            self.assertTrue(False)

    def test_getusimaid(self):
        usim = self.usim
        usim.reset()

        aid = 'A0000000871002FF86FF0289060100FF'
        aid1= usim.getusimaid()
        self.assertTrue(aid1==aid)
        r, sw = usim.selectbyaid(aid)
        self.assertTrue(r!='')
        self.assertTrue(sw==SW_NO_ERROR)

    def test_selectbyaid(self):
        usim = self.usim
        usim.reset()

        aid = 'A0000000871002FF86FF0289060100FF'
        r, sw = usim.selectbyaid(aid)
        self.assertTrue(r!='')
        self.assertTrue(sw==SW_NO_ERROR)
        r, sw = usim.selectbyaid(aid, nofcp=True)
        self.assertTrue(r=='')
        self.assertTrue(sw==SW_NO_ERROR)
        r, sw = usim.selectbyaid(aid, nofcp=False)
        self.assertTrue(r!='')
        self.assertTrue(sw==SW_NO_ERROR)

        aid = 'A0000000871004FF86FFFF89060100FF'
        r, sw = usim.selectbyaid(aid)
        self.assertTrue(r!='')
        self.assertTrue(sw==SW_NO_ERROR)
        r, sw = usim.selectbyaid(aid, nofcp=True)
        self.assertTrue(r=='')
        self.assertTrue(sw==SW_NO_ERROR)
        r, sw = usim.selectbyaid(aid, nofcp=False)
        self.assertTrue(r!='')
        self.assertTrue(sw==SW_NO_ERROR)

    def test_select(self):
        usim = self.usim
        usim.reset()
        r, sw = usim.select('3F00')
        self.assertTrue(r!='')
        self.assertTrue(sw==SW_NO_ERROR)
        r, sw = usim.select('2FE2')
        self.assertTrue(r!='')
        self.assertTrue(sw==SW_NO_ERROR)
        r, sw = usim.select('2F00')
        self.assertTrue(r!='')
        self.assertTrue(sw==SW_NO_ERROR)

        r, sw = usim.select('3F00', nofcp=False)
        self.assertTrue(r!='')
        self.assertTrue(sw==SW_NO_ERROR)
        r, sw = usim.select('2FE2', nofcp=False)
        self.assertTrue(r!='')
        self.assertTrue(sw==SW_NO_ERROR)
        r, sw = usim.select('2F00', nofcp=False)
        self.assertTrue(r!='')
        self.assertTrue(sw==SW_NO_ERROR)

        r, sw = usim.select('3F00', nofcp=True)
        self.assertTrue(r=='')
        self.assertTrue(sw==SW_NO_ERROR)
        r, sw = usim.select('2FE2', nofcp=True)
        self.assertTrue(r=='')
        self.assertTrue(sw==SW_NO_ERROR)
        r, sw = usim.select('2F00', nofcp=True)
        self.assertTrue(r=='')
        self.assertTrue(sw==SW_NO_ERROR)

    def test_readrecord(self):
        usim = self.usim
        usim.reset()
        usim.select('3F00')
        usim.select('2F00')
        r, sw = usim.readrecord(1, 0x26)
        self.assertTrue(r!='')
        self.assertTrue(sw==SW_NO_ERROR)
        r, sw = usim.readrecord(2, 0x26)
        self.assertTrue(r!='')
        self.assertTrue(sw==SW_NO_ERROR)

    def test_readbinary(self):
        usim = self.usim
        usim.reset()
        usim.select('3F00')
        usim.select('2FE2')
        for i in range(10):
            r, sw = usim.readbinary(i, 10-i)
            self.assertTrue(r!='')
            self.assertTrue(sw==SW_NO_ERROR)

#----------------------------------------------------------------------------
if __name__ == '__main__':
    #FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    #logging.basicConfig(level=logging.DEBUG, format=FORMAT)

    # 测试条件：4700F读卡器 + 插入XH USIM卡一张
    name = r'Identiv uTrust 4700 F Contact Reader 2'
    api_pcsc.connectreader(name)
    unittest.main()

