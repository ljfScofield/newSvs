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
        
    def getAlgorithm(self):
        return api_pcsc.send('0007000001' , name='getAlgorithm')
        
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

    def test_0_buildKey(self):
        ''' test if all 3-des-key-length are supported '''
        des = self.des
        des.select()
        for i, x in enumerate((64, 128, 192)):
            r, sw = des.buildKey(i, x)
            if sw=='9000':
                self.logger.info('DESKEY length %d supported' %x)
            else:
                self.logger.info('DESKEY length %d NOT supported' %x)
                
    def test_1_buildCipher(self):
        ''' test if all 8-modepadding are supported '''
        des = self.des
        des.select()
        allsupported = True
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
            r, sw = des.buildCipher(i, value)
            #self.assertEqual(sw, '9000', 'cipher pading NOT supported %s' %name)
            if sw=='9000':
                self.logger.info('cipher pading supported %s' %name)
            else:
                allsupported = False
                self.logger.info('cipher pading NOT supported %s' %name)
                
        if not allsupported:
            self.fail("NOT all 8 modes are supported")
            
    def test_setKey(self):
        ''' test if setKey is supported '''
        des = self.des
        des.select()
        for i, x in enumerate((64, 128, 192)):
            r, sw = des.setKey(i, '00'*(x/8))
            if sw != '9000':
                self.logger.info('seticv fail')
            
    def test_seticv(self):
        ''' set icv '''
        des = self.des
        des.select()
        icv = '0101010101010101'
        r, sw = des.seticv(icv)
        if sw == '9000':
            self.logger.info('seticv success')
        else:
            self.logger.info('seticv fail')
    
    def test_chooseKey(self):
        ''' set chooseKey '''
        des = self.des
        des.select()
        nkey = 0x00
        r, sw = des.chooseKey(nkey)
        if sw == '9000':
            self.logger.info('chooseKey success')
        else:
            self.logger.info('chooseKey fail %s',sw)
         
    def test_initEnc(self):
        ''' test if init enc is supported '''
        des = self.des
        des.select()
        