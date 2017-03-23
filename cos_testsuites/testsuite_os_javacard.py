#!/usr/env python
# -*- coding: utf-8 -*-

""" 检测JavaCard标准中未明确的特性、边界条件

This script will check if personalization data compliants with customer requirment.

__author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
__date__ = "Aug 2016"
__version__ = "0.1.0"

Copyright 2016 XH Smart Card Co,. Ltd

Author: wg@china-xinghan.com
"""

import logging, os, webbrowser, unittest

import api_pcsc
import api_util
import api_unittest

import api_gp

#----------------------------------------------------------------------------
u = api_util.u
swap = api_util.swap

#----------------------------------------------------------------------------
class ALG_PSEUDO_RANDOM(object):
    ''' javacard.security.RandomData.ALG_PSEUDO_RANDOM '''

    def getcappath(self):
        cap = "ALG_PSEUDO_RANDOM.cap"
        return api_unittest.getcappath(cap)

    def getaids(self):
        instance, pkg, applet = 'C8C2B625CC6A785A5389D9C9F4E20101', 'C8C2B625CC6A785A5389D9C9F4E201', 'C8C2B625CC6A785A5389D9C9F4E20100'
        return instance, pkg, applet

    def select(self):
        instance, pkg, applet = self.getaids()
        api_gp.select(instance)

    def generateData(self, lgth):
        r, sw = api_pcsc.send('00000000%.2X' % (lgth&0xFF,), expectSW='9000', name='generate Data')
        return r

    def setseed(self, seed):
        ''' seed should be hexdigits string '''
        lgth = len(seed)/2
        r, sw = api_pcsc.send('00010000%.2X%s' % (lgth&0xFF, seed.upper()), expectSW='9000', name='set SEED')
        return self # return self to enable chain-operation

class TestCase_ALG_PSEUDO_RANDOM(api_unittest.TestCase):
    ''' 检测 javacard.security.RandomData.ALG_PSEUDO_RANDOM '''

    @classmethod
    def setUpClass(cls):
        # delete, load, install
        alg = ALG_PSEUDO_RANDOM()
        instance, pkg, applet = alg.getaids()

        api_pcsc.connectreader()
        api_gp.card()
        api_gp.auth()
        api_gp.deleteaid(pkg, True, expectSW='') # omit delete result
        api_gp.upload(alg.getcappath(), pkg)
        api_gp.install(instance, pkg, applet)

        cls.alg = alg

    @classmethod
    def tearDownClass(cls):
        instance, pkg, applet = cls.alg.getaids()
        api_pcsc.connectreader()
        api_gp.card()
        api_gp.auth()
        api_gp.deleteaid(pkg, True, expectSW='9000')
        cls.alg = None
        api_pcsc.disconnect()

    def setUp(self):
        ''' the testing framework will automatically call for us when we run the test
            
            setUp()和tearDown()会在调用test_XXXX()方法时都会被调用，即会被调用多次。

            unittest将new一个class instance，然后调用setUp()，再调用某个test_XXXX()f方法，再调用tearDown()方法。
            重复多次以执行所有test_XXXX()方法。
        '''
        pass

    def tearDown(self):
        pass

    def test_same_seed(self):
        ''' 对于相同的随机数种子，产生的随机数序列是否相同 '''
        alg = self.alg
        alg.select()

        # 'The random number sequence generated by this algorithm need not be the same even if seeded with the same seed data.'
        sample1 = ''.join([alg.setseed('%.2X'%i).generateData(i) for i in range(0,256)])
        sample2 = ''.join([alg.setseed('%.2X'%i).generateData(i) for i in range(0,256)])
        if sample1 == sample2:
            self.logger.info(u'对于相同的随机数种子，产生的随机数序列相同')
        else:
            self.logger.info(u'对于相同的随机数种子，产生的随机数序列不相同')
    

    def test_reset(self):
        ''' 每次复位之后，生成的随机数是否相同 '''
        alg = self.alg
        alg.select()

        # 'The random number sequence generated by this algorithm need not be the same even if seeded with the same seed data.'
        api_pcsc.reset()
        alg.select()
        data1 = alg.generateData(1)
        api_pcsc.reset()
        alg.select()
        data2 = alg.generateData(1)
        if data1 == data2:
            self.logger.info(u'每次复位之后，产生的随机数序列相同')
        else:
            self.logger.info(u'每次复位之后，产生的随机数序列不相同')

#----------------------------------------------------------------------------
class ALG_SECURE_RANDOM(object):
    ''' javacard.security.RandomData.ALG_SECURE_RANDOM '''

    def getcappath(self):
        cap = "ALG_SECURE_RANDOM.cap"
        return api_unittest.getcappath(cap)

    def getaids(self):
        instance, pkg, applet = '6EB2BEA52FA2BFD0A7EB9C914E9ADE01', '6EB2BEA52FA2BFD0A7EB9C914E9ADE', '6EB2BEA52FA2BFD0A7EB9C914E9ADE00'
        return instance, pkg, applet

    def select(self):
        instance, pkg, applet = self.getaids()
        api_gp.select(instance)

    def generateData(self, lgth):
        return api_pcsc.send('00000000%.2X' % (lgth&0xFF), expectSW='9000', name='generateData')

    def setseed(self, seed):
        ''' seed should be hexdigits string '''
        lgth = len(seed)/2
        r, sw = api_pcsc.send('00010000%.2X%s' % (lgth&0xFF, seed.upper()), expectSW='9000', name='setseed')
        return self # return self to enable chain-operation

class TestCase_ALG_SECURE_RANDOM(api_unittest.TestCase):
    ''' 检测 javacard.security.RandomData.ALG_SECURE_RANDOM '''

    @classmethod
    def setUpClass(cls):
        # delete, load, install
        alg = ALG_SECURE_RANDOM()
        instance, pkg, applet = alg.getaids()

        api_pcsc.connectreader()
        api_gp.card()
        api_gp.auth()
        api_gp.deleteaid(pkg, True, expectSW='') # omit delete result
        api_gp.upload(alg.getcappath(), pkg)
        api_gp.install(instance, pkg, applet)

        cls.alg = alg
        api_pcsc.disconnect()

    @classmethod
    def tearDownClass(cls):
        instance, pkg, applet = cls.alg.getaids()
        api_pcsc.connectreader()
        api_gp.card()
        api_gp.auth()
        api_gp.deleteaid(pkg, True, expectSW='9000')
        cls.alg = None
        api_pcsc.disconnect()

    def setUp(self):
        api_pcsc.connectreader()

    def tearDown(self):
        api_pcsc.disconnect()

    def test_same_seed(self):
        ''' 对于相同的随机数种子，产生的随机数序列是否相同 '''
        alg = self.alg
        alg.select()

        # 'The random number sequence generated by this algorithm need not be the same even if seeded with the same seed data.'
        sample1 = ''.join([alg.setseed('%.2X'%i).generateData(i)[0] for i in range(0,256)])
        sample2 = ''.join([alg.setseed('%.2X'%i).generateData(i)[0] for i in range(0,256)])
        if sample1 == sample2:
            self.logger.info(u'对于相同的随机数种子，产生的随机数序列相同')
        else:
            self.logger.info(u'对于相同的随机数种子，产生的随机数序列不相同')
    
    def test_reset(self):
        ''' 每次复位之后，生成的随机数是否相同 '''
        alg = self.alg
        alg.select()

        # 'The random number sequence generated by this algorithm need not be the same even if seeded with the same seed data.'
        api_pcsc.reset()
        alg.select()
        data1 = alg.generateData(1)[0]
        api_pcsc.reset()
        alg.select()
        data2 = alg.generateData(1)[0]
        if data1 == data2:
            self.logger.info(u'每次复位之后，产生的随机数序列相同')
        else:
            self.logger.info(u'每次复位之后，产生的随机数序列不相同')

    def test_sp80022rev1a(self):
        ''' http://csrc.nist.gov/groups/ST/toolkit/rng/documentation_software.html
        '''
        self.logger.info(u'Todo')

#----------------------------------------------------------------------------
class JCSystem(object):
    ''' javacard.framework.JCSystem '''

    CLEAR_ON_DESELECT = 0x01
    def getcappath(self):
        cap = "jcsystem.cap"
        return api_unittest.getcappath(cap)

    def getaids(self):
        instance, pkg, applet = '475ece4587566e09a007db80abec8701', '475ece4587566e09a007db80abec87', '475ece4587566e09a007db80abec8700'
        return instance, pkg, applet

    def select(self):
        instance, pkg, applet = self.getaids()
        api_gp.select(instance)

    def abortTransaction(self):
        return api_pcsc.send('0000000000', name='abortTransaction')
        
    def beginTransaction(self):
        return api_pcsc.send('0001000000', name='beginTransaction')
        
    def commitTransaction(self):
        return api_pcsc.send('0002000000', name='commitTransaction')
        
    def getAID(self):
        return api_pcsc.send('0003000000', name='getAID')
        
    def getAppletShareableInterfaceObject(self):
        return api_pcsc.send('0004000000', name='getAppletShareableInterfaceObject')
        
    def getAssignedChannel(self):
        return api_pcsc.send('0005000000', name='getAssignedChannel')
        
    def getAvailableMemory(self, memoryType):
        return api_pcsc.send('0006000001%.2X'%memoryType, name='getAvailableMemory')

    def getMaxCommitCapacity(self):
        return api_pcsc.send('0007000002', name='getMaxCommitCapacity')
        
    def getPreviousContextAID(self):
        return api_pcsc.send('0008000000', name='getPreviousContextAID')
        
    def getTransactionDepth(self):
        return api_pcsc.send('0009000001', name='getTransactionDepth')
        
    def getUnusedCommitCapacity(self):
        return api_pcsc.send('000A000002', name='getUnusedCommitCapacity')
        
    def getVersion(self):
        return api_pcsc.send('000B000002', name='getVersion')
        
    def isAppletActive(self, theApplet):
        return api_pcsc.send('000C0000%.2X%s' % (len(theApplet)/2, theApplet), name='isAppletActive')
        
    def isObjectDeletionSupported(self):
        return api_pcsc.send('000D000001', name='isObjectDeletionSupported')

    def isTransient(self):
        return api_pcsc.send('000E000000', name='isTransient')
        
    def lookupAID(self, aid):
        return api_pcsc.send('000F0000%.2X%s' % (len(aid)/2, aid), name='lookupAID')
        
    def makeTransientBooleanArray(self, length, event):
        return api_pcsc.send('0010000003%.4X%.2X' % (length, event), name='makeTransientBooleanArray')
        
    def makeTransientByteArray(self, length, event):
        return api_pcsc.send('0011000003%.4X%.2X' % (length, event), name='makeTransientByteArray')
        
    def makeTransientObjectArray(self, length, event):
        return api_pcsc.send('0012000003%.4X%.2X' % (length, event), name='makeTransientObjectArray')

    def makeTransientShortArray(self, length, event):
        return api_pcsc.send('0013000003%.4X%.2X' % (length, event), name='makeTransientShortArray')
        
    def requestObjectDeletion(self):
        return api_pcsc.send('0014000000', name='requestObjectDeletion')
        
    def newEEPROM(self,length):
        return api_pcsc.send('0015000002%.4X' % (length), name='newEEPROM')

class TestCase_JCSystem(api_unittest.TestCase):
    ''' 检测 javacard.framework.JCSystem 
        MEMORY_TYPE_PERSISTENT = 0;
        CLEAR_ON_RESET = 1;
        CLEAR_ON_DESELECT = 2;
    '''

    @classmethod
    def setUpClass(cls):
        # delete, load, install
        jcs = JCSystem()
        instance, pkg, applet = jcs.getaids()

        api_pcsc.connectreader()
        api_gp.card()
        api_gp.auth()
        api_gp.deleteaid(pkg, True, expectSW='') # omit delete result
        api_gp.upload(jcs.getcappath(), pkg)
        api_gp.install(instance, pkg, applet)

        cls.jcs = jcs

    @classmethod
    def tearDownClass(cls):
        instance, pkg, applet = cls.jcs.getaids()
        api_pcsc.connectreader()
        api_gp.card()
        api_gp.auth()
        api_gp.deleteaid(pkg, True, expectSW='9000')
        cls.jcs = None
        api_pcsc.disconnect()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_requestObjectDeletion(self):
        ''' 测试 requestObjectDeletion'''
        jcs = self.jcs
        jcs.select()

        r, sw = jcs.requestObjectDeletion()
        if r != '':
            self.logger.info(u'不应有响应数据返回：%s' % r)

        if sw == '9000':
            self.logger.info(u'支持requestObjectDeletion')
        else:
            self.logger.info(u'不支持requestObjectDeletion: %s' % sw)
        
        if r!='' or sw!='9000':
            self.fail(u'requestObjectDeletion不支持')
            
    def test_getAvailableMemory(self):
        ''' 测试 getAvailableMemory '''
        jcs = self.jcs
        jcs.select()
        
        r, sw = jcs.getAvailableMemory(00)
        if r == '':
            self.fail(u'应有响应数据返回!')        
        if sw == '9000':
            self.logger.info(u'测试getAvailableMemory，查询EEPROM的大小 : %s' % r) 
        else:
            self.fail(u'测试getAvailableMemory，查询EEPROM的大小失败')        

        r, sw = jcs.getAvailableMemory(0x01)
        if r == '':
            self.fail(u'应有响应数据返回!')
        if sw == '9000':
            self.logger.info(u'测试getAvailableMemory查询COR成功,大小：%s' % r)
        else:
            self.fail(u'测试getAvailableMemory查询COR失败 : %s' % sw)            
            
        r, sw = jcs.getAvailableMemory(0x02)
        if r == '':
            self.fail(u'应有响应数据返回!')
        if sw == '9000':
            self.logger.info(u'测试getAvailableMemory查询COD成功,大小：%s' % r)
        else:
            self.fail(u'测试getAvailableMemory查询COD失败 : %s' % sw)            
            
    def test_getMaxCommitCapacity(self):
        ''' 测试 getMaxCommitCapacity 
        '''
        jcs = self.jcs
        jcs.select()

        r, sw = jcs.getMaxCommitCapacity()
        if r == '':
            self.logger.fail(u'应有响应数据返回!')

        if sw == '9000':
            self.logger.info(u'测试 getMaxCommitCapacity 查询成功,事务保护区大小：%s' %r)
        else:
            self.fail(u'测试 getMaxCommitCapacity 查询失败 : %s' % sw)
                                    
                                    
    def test_makeTransientByteArray(self):
        ''' 测试makeTransientByteArray
        '''
        jcs = self.jcs
        jcs.select()
        #申请COR
        r, sw = jcs.makeTransientByteArray(0x0002,0x01)
        if r != '':
            self.logger.info(u'有响应数据返回,申请%s个Byte类型的COR' % r)

        if sw == '9000':
            self.logger.info(u'支持makeTransientByteArray')
        else:
            self.fail(u'不支持makeTransientByteArray : %s' % sw)
                
        r, sw = jcs.getAvailableMemory(0x01)
        if r == '':
            self.fail(u'应有响应数据返回!')
        if sw == '9000':
            self.logger.info(u'查询剩余COR成功,大小：%s' % r)
        else:
            self.fail(u'查询剩余COR失败 : %s' % sw)
            
        #申请COD
        r, sw = jcs.makeTransientByteArray(0x0002,0x02)
        if r != '':
            self.logger.info(u'有响应数据返回,申请%s个Byte类型的COD' % r)

        if sw == '9000':
            self.logger.info(u'支持makeTransientByteArray')
        else:
            self.fail(u'不支持makeTransientByteArray : %s' % sw)
                
        r, sw = jcs.getAvailableMemory(0x02)
        if r == '':
            self.fail(u'应有响应数据返回!')
        if sw == '9000':
            self.logger.info(u'查询剩余COD成功,大小：%s' % r)
        else:
            self.fail(u'查询剩余COD失败 : %s' % sw)
            
    def test_makeTransientBooleanArray(self):
        ''' 测试makeTransientBooleanArray
        '''
        jcs = self.jcs
        jcs.select()
        #查询COR、COD
        r, sw = jcs.getAvailableMemory(0x01)
        if (r != '') and (sw == '9000'):
            self.logger.info(u'COR大小：%s ' %r)
            
        r, sw = jcs.getAvailableMemory(0x02)
        if (r != '') and (sw == '9000'):
            self.logger.info(u'COD大小：%s ' %r)
        
        #申请COR
        r, sw = jcs.makeTransientBooleanArray(0x0002,0x01)
        if r != '':
            self.logger.info(u'有响应数据返回,申请%s个Boolean类型的COR' % r)

        if sw == '9000':
            self.logger.info(u'支持 makeTransientBooleanArray')
        else:
            self.fail(u'不支持 makeTransientBooleanArray : %s' % sw)
                
        r, sw = jcs.getAvailableMemory(0x01)
        if sw == '9000':
            self.logger.info(u'查询剩余COR成功,大小：%s' % r)
        else:
            self.fail(u'查询剩余COR失败 : %s' % sw)
            
        #申请COD
        r, sw = jcs.makeTransientBooleanArray(0x0002,0x02)
        if r != '':
            self.logger.info(u'有响应数据返回,申请%s个Boolean类型的COD' % r)

        if sw == '9000':
            self.logger.info(u'支持 makeTransientBooleanArray')
        else:
            self.fail(u'不支持 makeTransientBooleanArray : %s' % sw)
                
        r, sw = jcs.getAvailableMemory(0x02)
        if sw == '9000':
            self.logger.info(u'查询剩余COD成功,大小：%s' % r)
        else:
            self.fail(u'查询剩余COD失败 : %s' % sw)
            
    def test_makeTransientShortArray(self):
        ''' 测试makeTransientShortArray
        '''
        jcs = self.jcs
        jcs.select()
        #查询COR、COD
        r, sw = jcs.getAvailableMemory(0x01)
        if (r != '') and (sw == '9000'):
            self.logger.info(u'COR大小：%s ' %r)
            
        r, sw = jcs.getAvailableMemory(0x02)
        if (r != '') and (sw == '9000'):
            self.logger.info(u'COD大小：%s ' %r)
        
        #申请COR
        r, sw = jcs.makeTransientShortArray(0x0002,0x01)
        if r != '':
            self.logger.info(u'有响应数据返回,申请%s个Short类型的COR' % r)

        if sw == '9000':
            self.logger.info(u'支持makeTransientShortArray')
        else:
            self.fail(u'不支持makeTransientShortArray : %s' % sw)
                
        r, sw = jcs.getAvailableMemory(0x01)
        if sw == '9000':
            self.logger.info(u'查询剩余COR成功,大小：%s' % r)
        else:
            self.fail(u'查询剩余COR失败 : %s' % sw)
            
        #申请COD
        r, sw = jcs.makeTransientByteArray(0x0002,0x02)
        if r != '':
            self.logger.info(u'有响应数据返回,申请%s个Short类型的COD' % r)

        if sw == '9000':
            self.logger.info(u'支持makeTransientShortArray')
        else:
            self.fail(u'不支持makeTransientShortArray : %s' % sw)
                
        r, sw = jcs.getAvailableMemory(0x02)
        if sw == '9000':
            self.logger.info(u'查询剩余COD成功,大小：%s' % r)
        else:
            self.fail(u'查询剩余COD失败 : %s' % sw)
                        
    def test_makeTransientObjectArray(self):
        ''' 测试makeTransientObjectArray
        '''
        jcs = self.jcs
        jcs.select()
        #查询COR、COD
        r, sw = jcs.getAvailableMemory(0x01)
        if (r != '') and (sw == '9000'):
            self.logger.info(u'COR大小：%s ' %r)
            
        r, sw = jcs.getAvailableMemory(0x02)
        if (r != '') and (sw == '9000'):
            self.logger.info(u'COD大小：%s ' %r)
        
        #申请COR
        r, sw = jcs.makeTransientObjectArray(0x0002,0x01)
        if r != '':
            self.logger.info(u'有响应数据返回,申请%s个Object类型的COR' % r)

        if sw == '9000':
            self.logger.info(u'支持makeTransientObjectArray')
        else:
            self.fail(u'不支持makeTransientObjectArray : %s' % sw)
                
        r, sw = jcs.getAvailableMemory(0x01)
        if sw == '9000':
            self.logger.info(u'查询剩余COR成功,大小：%s' % r)
        else:
            self.fail(u'查询剩余COR失败 : %s' % sw)
            
        #申请COD
        r, sw = jcs.makeTransientObjectArray(0x0002,0x02)
        if r != '':
            self.logger.info(u'有响应数据返回,申请%s个Object类型的COD' % r)

        if sw == '9000':
            self.logger.info(u'支持makeTransientObjectArray')
        else:
            self.fail(u'不支持makeTransientObjectArray : %s' % sw)
                
        r, sw = jcs.getAvailableMemory(0x02)
        if sw == '9000':
            self.logger.info(u'查询剩余COD成功,大小：%s' % r)
        else:
            self.fail(u'查询剩余COD失败 : %s' % sw)
                                                
    def test_newEEPROM(self):
        ''' 测试 newEEPROM '''
        jcs = self.jcs
        jcs.select()
        
        r1, sw1 = jcs.getAvailableMemory(00)
        if r1 == '':
            self.fail(u'应有响应数据返回!')
        if sw1 == '9000':
            self.logger.info(u'查询EEPROM的大小 : %s' % r1) 
        else:
            self.fail(u'查询EEPROM的大小失败')
        
        for i in range(10):
            r, sw = jcs.newEEPROM(0x0001)
            if sw == '9000':
                self.logger.info(u'申请1个Byte EEPROM 成功: %s' % r) 
            else:
                self.fail(u'申请1个Byte EEPROM 失败')            
            r, sw = jcs.getAvailableMemory(00)
            if sw == '9000':
                self.logger.info(u'查询EEPROM的剩余大小 : %s' % r) 
            else:
                self.fail(u'查询EEPROM的剩余大小失败')
        

#----------------------------------------------------------------------------
def main():
    classes = (
        TestCase_ALG_PSEUDO_RANDOM, 
        TestCase_ALG_SECURE_RANDOM, 
        TestCase_JCSystem,
        )
    testsuite = unittest.TestSuite([api_unittest.TestLoader().loadTestsFromTestCase(clz) for clz in classes])
    title = u'COS_JavaCard'
    description = u'检测JavaCard标准中未明确的特性、边界条件'
    path = os.path.abspath('testsuite_os_javacard.html')
    level = logging.INFO # 输入日记的多少, DEBUG时最多 INFO/ERROR/CRITICAL
    verbosity = 0 # 命令行窗口的输出详细程度 0/1/2 从少到多 设定为2时可以调试一些非测试案例出错的情况

    testresult = api_unittest.htmlunittest(testsuite, title, description, path, level, verbosity)
    webbrowser.open('file://'+path)

#----------------------------------------------------------------------------
if __name__ == '__main__':
    main()
