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
import random

import api_gp


class DESKEY(object):
    ''' javacard.security.DESKey '''
    def getcappath(self):
        cap = "DesKeyTest.cap"
        return api_unittest.getcappath(cap)
        
    def getaids(self):
        instance, pkg, applet = '010203040506', '0102030405', '010203040506'
        return instance, pkg, applet

    def select(self):
        instance, pkg, applet = self.getaids()
        api_gp.select(instance)
        
    def setKey(self, mode, val):   #0 : des_64 1:des_128 2:des_192
        return api_pcsc.send('0000%.2X00%.2X%s' %(mode,len(val)/2,val), name='setkey')
    
    def seticv(self, icv):
        return api_pcsc.send('0001000008%s' %icv, name='seticv')

    def chooseKey(self, nkey):         #0 : des_64 1:des_128 2:des_192
        return api_pcsc.send('0002%.2X0000' %nkey, name='chooseKey')
        
    def initEnc(self, mode, paddingMode):         
        return api_pcsc.send('0003%.2X%.2X00' %(mode,paddingMode), name='initEnc')
        
    def initDec(self, mode, paddingMode): 
        return api_pcsc.send('0004%.2X%.2X00' %(mode,paddingMode), name='initDec')
        
    def dofinal(self, data):
        return api_pcsc.send('00050000%.2X%s' %(len(data)/2,data), name='dofinal')
        
    def update(self):
        return api_pcsc.send('0006000000' , name='update')
        
    def getAlgorithm(self, mode):
        return api_pcsc.send('000700%.2X01' %mode ,name='getAlgorithm')
        
    def clearKey(self, nkey):         #0 : des_64 1:des_128 2:des_192
        return api_pcsc.send('0008%.2X0000' %nkey , name='clearKey')
     
    def buildKey(self, deskey, key_lgth):
        return api_pcsc.send('0009%.2X%.2X00' %(deskey, key_lgth) , name='buildKey')
        
    def buildCipher(self, cipher, mode):
        return api_pcsc.send('000A%.2X%.2X00' %(cipher, mode) , name='buildcipher')
#----------------------------------------------------------------------------  


#################################################################
class TestCase_DESKEY(api_unittest.TestCase):
    ''' javacard.security.DESKey  8 type mode of paddingMode and 3 type security key        
    '''
    @classmethod
    def setUpClass(cls):
        # delete, load, install
        des = DESKEY()
        instance, pkg, applet = des.getaids()

        api_pcsc.connectreader()
        api_gp.card()
        api_gp.auth()
        api_gp.deleteaid(pkg, True, expectSW='') # omit delete result
        api_gp.upload(des.getcappath(), pkg)
        api_gp.install(instance, pkg, applet)

        cls.des = des

    @classmethod
    def tearDownClass(cls):
        instance, pkg, applet = cls.des.getaids()
        api_pcsc.connectreader()
        api_gp.card()
        api_gp.auth()
        api_gp.deleteaid(pkg, True, expectSW='9000')
        cls.des = None
        api_pcsc.disconnect()

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_00_buildKey_64des(self, index=0, lgth=64, label = '64des'):
        des = self.des
        des.select()
        r, sw = des.buildKey(index, lgth)
        self.assertEqual(sw, '9000', label + ' not supported')
        
    def test_01_buildKey_128des(self, index=1, lgth=128 , label = '128des'):
        self.test_00_buildKey_64des(index,lgth,label)
    
    def test_02_buildKey_192des(self, index=2, lgth= 192 , label = '192des'):
        self.test_00_buildKey_64des(index,lgth,label)
    
    
    def test_11_getInstance_ALG_DES_CBC_NOPAD(self, index=0, alg=1, label='ALG_DES_CBC_NOPAD'):
        des = self.des
        des.select()
        r, sw = des.buildCipher(index, alg)
        self.assertEqual(sw, '9000', label + ' not supported')
            
    def test_12_getInstance_ALG_DES_CBC_ISO9797_M1(self, index=1, alg=2, label='ALG_DES_CBC_ISO9797_M1'):
        self.test_11_getInstance_ALG_DES_CBC_NOPAD(index, alg, label)
                  
    def test_13_getInstance_ALG_DES_CBC_ISO9797_M2(self, index=2, alg=3, label='ALG_DES_CBC_ISO9797_M2'):
        self.test_11_getInstance_ALG_DES_CBC_NOPAD(index, alg, label)
        
    def test_14_getInstance_ALG_DES_CBC_ISO9797_M1(self, index=3, alg=4, label='ALG_DES_CBC_PKCS5'):
        self.test_11_getInstance_ALG_DES_CBC_NOPAD(index, alg, label)
                  
    def test_15_getInstance_ALG_DES_ECB_NOPAD(self, index=4, alg=5, label='ALG_DES_ECB_NOPAD'):
        self.test_11_getInstance_ALG_DES_CBC_NOPAD(index, alg, label)
    
    def test_16_getInstance_ALG_DES_ECB_ISO9797_M1(self, index=5, alg=6, label='ALG_DES_ECB_ISO9797_M1'):
        self.test_11_getInstance_ALG_DES_CBC_NOPAD(index, alg, label)
        
    def test_17_getInstance_ALG_DES_ECB_ISO9797_M2(self, index=6, alg=7, label='ALG_DES_ECB_ISO9797_M2'):
        self.test_11_getInstance_ALG_DES_CBC_NOPAD(index, alg, label)
        
    def test_18_getInstance_ALG_DES_ECB_PKCS5(self, index=7, alg=8, label='ALG_DES_ECB_PKCS5'):
        self.test_11_getInstance_ALG_DES_CBC_NOPAD(index, alg, label)
                  
    def test_19_setKey(self):
        ''' test if setKey is supported '''
        des = self.des
        des.select()
        for i, x in enumerate((64, 128, 192)):
            r, sw = des.setKey(i, '00'*(x/8))
            if sw != '9000':
                self.logger.info('seticv fail')
            
    def test_20_seticv(self):
        ''' set icv '''
        des = self.des
        des.select()
        lst = ['%.2X'%random.randint(0,255) for i in range(8)]
        icv = ''.join(lst)
        r, sw = des.seticv(icv)
        if sw == '9000':
            self.logger.info('seticv success')
        else:
            self.logger.info('seticv fail')

    def test_22_getAlgorithm(self):
        ''' test if supported getAlgorithm'''
        des = self.des
        des.select()
        for i, t in enumerate((
            ('ALG_DES_CBC_NOPAD', 0x1), 
            ('ALG_DES_CBC_ISO9797_M1', 0x2), 
            ('ALG_DES_CBC_ISO9797_M2', 0x3), 
            ('ALG_DES_CBC_PKCS5', 0x4), 
            ('ALG_DES_ECB_NOPAD', 0x5), 
            ('ALG_DES_ECB_ISO9797_M1', 0x6),
            ('ALG_DES_ECB_ISO9797_M2', 0x7), 
            ('ALG_DES_ECB_PKCS5', 0x8),
            )):
            name, value = t
            des.buildCipher(i, value)
            r, sw = des.getAlgorithm(i)
            if sw == '9000':
                self.logger.info('getAlgorithm success %s call %s',r ,name)
            else:
                self.logger.info('getAlgorithm fail ')
                
    def test_23_initEnc_cbc(self):
        ''' test if init is supported'''
        des = self.des
        des.select()    
        for i, t in enumerate((
            ('ALG_DES_CBC_NOPAD', 0x1), 
            ('ALG_DES_CBC_ISO9797_M1', 0x2), 
            ('ALG_DES_CBC_ISO9797_M2', 0x3), 
            ('ALG_DES_CBC_PKCS5', 0x4), 
            )):
            name, value = t
            for j in range(3):
                des.chooseKey(j)
                r,sw = des.initEnc(0x00,i)
                if sw == '9000':
                    self.logger.info('init enc_cbc success %s', name)
                else:
                    self.logger.info('init enc_cbc fail %s', name)

    def test_24_initEnc_ebc(self):
        ''' test if init is supported'''
        des = self.des
        des.select()
        for i, t in enumerate((
            ('ALG_DES_ECB_NOPAD', 0x5), 
            ('ALG_DES_ECB_ISO9797_M1', 0x6), 
            ('ALG_DES_ECB_ISO9797_M2', 0x7), 
            ('ALG_DES_ECB_PKCS5', 0x8), 
            )):
            name, value = t
            for j in range(3):
                des.chooseKey(j)
                r,sw = des.initEnc(0x01,i+4)
                if sw == '9000':
                    self.logger.info('init enc_ecb success %s', name)
                else:
                    self.logger.info('init enc_ecb fail %s', name)
                    
    def test_25_dofinal_cbc(self):
        ''' test if dofinal is supported '''
        des = self.des
        des.select()
        lst = ['%.2X'%random.randint(0,255) for i in range(8)]
        buf = ''.join(lst)
        for i, t in enumerate((
            ('ALG_DES_ECB_NOPAD', 0x5), 
            ('ALG_DES_ECB_ISO9797_M1', 0x6), 
            ('ALG_DES_ECB_ISO9797_M2', 0x7), 
            ('ALG_DES_ECB_PKCS5', 0x8), 
            )):
            name, value = t
            for j in range(3):
                des.chooseKey(j)
                des.initEnc(0x01,i+4)
                r,sw = des.dofinal(buf)
                if sw == '9000':
                    self.logger.info('dofinal enc_cbc success %s', name)
                else:
                    self.logger.info('dafinal enc_cbc fail %s', name)
                    
    def test_26_dofinal_ecb(self):
        ''' test if dofinal is supported '''
        des = self.des
        des.select()
        lst = ['%.2X'%random.randint(0,255) for i in range(8)]
        buf = ''.join(lst)
        for i, t in enumerate((
            ('ALG_DES_ECB_NOPAD', 0x5), 
            ('ALG_DES_ECB_ISO9797_M1', 0x6), 
            ('ALG_DES_ECB_ISO9797_M2', 0x7), 
            ('ALG_DES_ECB_PKCS5', 0x8), 
            )):
            name, value = t
            for j in range(3):
                des.chooseKey(j)
                des.initEnc(0x01,i+4)
                r,sw = des.dofinal(buf)
                if sw == '9000':
                    self.logger.info('dofinal enc_ecb success %s', name)
                else:
                    self.logger.info('dafinal enc_ecb fail %s', name)
                    
                    
    def test_27_dec_dofinal_cbc(self):
        ''' test if dofinal is supported '''
        des = self.des
        des.select()
        lst = ['%.2X'%random.randint(0,255) for i in range(8)]
        buf = ''.join(lst)
        for i, t in enumerate((
            ('ALG_DES_ECB_NOPAD', 0x5), 
            ('ALG_DES_ECB_ISO9797_M1', 0x6), 
            ('ALG_DES_ECB_ISO9797_M2', 0x7), 
            ('ALG_DES_ECB_PKCS5', 0x8), 
            )):
            name, value = t
            for j in range(3):
                des.chooseKey(j)
                des.initDec(0x01,i+4)
                r,sw = des.dofinal(buf)
                if sw == '9000':
                    self.logger.info('dofinal enc_cbc success %s', name)
                else:
                    self.logger.info('dafinal enc_cbc fail %s', name)
                    
    def test_28_dec_dofinal_ecb(self):
        ''' test if dofinal is supported '''
        des = self.des
        des.select()
        lst = ['%.2X'%random.randint(0,255) for i in range(8)]
        buf = ''.join(lst)
        for i, t in enumerate((
            ('ALG_DES_ECB_NOPAD', 0x5), 
            ('ALG_DES_ECB_ISO9797_M1', 0x6), 
            ('ALG_DES_ECB_ISO9797_M2', 0x7), 
            ('ALG_DES_ECB_PKCS5', 0x8), 
            )):
            name, value = t
            for j in range(3):
                des.chooseKey(j)
                des.initDec(0x01,i+4)
                r,sw = des.dofinal(buf)
                if sw == '9000':
                    self.logger.info('dofinal enc_ecb success %s', name)
                else:
                    self.logger.info('dafinal enc_ecb fail %s', name)
    
    
    def test_29_clearKey(self):
        ''' test if supported clearKey '''
        des = self.des
        des.select()   
        for j in range(3):
            r, sw = des.clearKey(j)
            self.assertEqual(sw, '9000', 'failed to clear key after setkey')    
            r, sw = des.clearKey(j)
            self.assertEqual(sw, '9000', 'failed to clear key again after clear key')    
            for i in range(10):
                r, sw = des.clearKey(j)
                self.assertEqual(sw, '9000', 'failed to clear key for 10 times')    
