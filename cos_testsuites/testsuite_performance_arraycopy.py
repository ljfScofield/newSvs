#!/usr/env python
# -*- coding: utf-8 -*-

""" Test Performance of Util.arrayCopy

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

TIMES = 100

#----------------------------------------------------------------------------
class Performace_arrayCopy(object):
    ''' Python adapter of TestCase_Performace_arrayCopy applet '''

    def getcappath(self):
        cap = "arrayCopy.cap"
        return api_unittest.getcappath(cap)

    def getaids(self):
        instance, pkg, applet = '9562DE12D4BBE9FFCE1082DA593D8000', '9562DE12D4BBE9FFCE1082DA593D80', '9562DE12D4BBE9FFCE1082DA593D8000'
        return instance, pkg, applet

    def select(self):
        instance, pkg, applet = self.getaids()
        return api_gp.select(instance)

    def arrayCopy(self, length, times):
        return api_pcsc.send('0000%.4X%.2X' % (length&0xFFFF, times&0xFF), expectSW='9000', name='arrayCopy(), %d bytes, %d times' % (length, times))

    def arrayCopyNonAtomic(self, length, times):
        return api_pcsc.send('0001%.4X%.2X' % (length&0xFFFF, times&0xFF), expectSW='9000', name='arrayCopy(), %d bytes, %d times' % (length, times))

    def arrayRandomize(self, length):
        return api_pcsc.send('0002%.4X00' % (length&0xFFFF), expectSW='9000', name='arrayRandomize(), %d bytes' % length)

    def sizeof(self):
        r, sw = self.select()
        s, s1 = int(r[:4], 16), int(r[4:], 16) # size of target 'array', source 'array1'
        return (s, s1)

    def do_arrayRandomize(self):
        ''' 根据select取得的array1大小值，将其randomize随机化
        '''
        s, s1 = self.sizeof()
        self.arrayRandomize(s1)

class TestCase_Performance_ArrayCopy(api_unittest.TestCase):
    ''' 检测 Util.arrayCopy 的性能
    '''

    @classmethod
    def setUpClass(cls):
        # delete, load, install
        app = Performace_arrayCopy()
        instance, pkg, applet = app.getaids()

        api_pcsc.connectreader()
        api_gp.card()
        api_gp.auth()
        api_gp.deleteaid(pkg, True, expectSW='') # omit delete result
        api_gp.upload(app.getcappath(), pkg)
        api_gp.install(instance, pkg, applet)

        api_pcsc.reset()
        cls.app = app

    @classmethod
    def tearDownClass(cls):
        instance, pkg, applet = cls.app.getaids()
        api_pcsc.connectreader()
        api_gp.card()
        api_gp.auth()
        api_gp.deleteaid(pkg, True, expectSW='9000')
        cls.app = None

        api_pcsc.disconnect()

    def setUp(self):
        r, sw = self.app.select()
        self.app.do_arrayRandomize()

    def tearDown(self):
        pass

    def _test_arrayCopy(self, length=0, times=TIMES):
        lst = []
        for n in range(0, times+1, 1):
            self.app.arrayCopy(length, n)
            t = api_pcsc.getexectime()
            avg = t/n if n!=0 else t
            lst.append( (t, avg) )

        avgs = map(lambda x:x[1], lst)
        return sum(avgs) / len(avgs)

    def test_0x000_bytes(self, length=0, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x001_bytes(self, length=1, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x002_bytes(self, length=2, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x004_bytes(self, length=4, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x008_bytes(self, length=8, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x010_bytes(self, length=0x10, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x020_bytes(self, length=0x20, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x030_bytes(self, length=0x30, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x040_bytes(self, length=0x40, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x050_bytes(self, length=0x50, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x060_bytes(self, length=0x60, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x070_bytes(self, length=0x70, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x080_bytes(self, length=0x80, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x090_bytes(self, length=0x90, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x0A0_bytes(self, length=0xA0, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x0B0_bytes(self, length=0xB0, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x0C0_bytes(self, length=0xC0, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x0D0_bytes(self, length=0xD0, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x0E0_bytes(self, length=0xE0, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x0F0_bytes(self, length=0xF0, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x100_bytes(self, length=0x100, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x110_bytes(self, length=0x110, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x120_bytes(self, length=0x120, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x130_bytes(self, length=0x130, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x140_bytes(self, length=0x140, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x150_bytes(self, length=0x150, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x160_bytes(self, length=0x160, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x170_bytes(self, length=0x170, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x180_bytes(self, length=0x180, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x190_bytes(self, length=0x190, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x1A0_bytes(self, length=0x1A0, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x1B0_bytes(self, length=0x1B0, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x1C0_bytes(self, length=0x1C0, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x1D0_bytes(self, length=0x1D0, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x1E0_bytes(self, length=0x1E0, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x1F0_bytes(self, length=0x1F0, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))
    def test_0x200_bytes(self, length=0x200, times=TIMES):
        t = self._test_arrayCopy(length=length, times=TIMES)
        self.logger.info('%.3f ms, %d bytes' % (t, lengthx))

#----------------------------------------------------------------------------
def main():
    classes = (
        TestCase_Performace_arrayCopy,
        )
    testsuite = unittest.TestSuite([api_unittest.TestLoader().loadTestsFromTestCase(clz) for clz in classes])
    title = u'Performace arrayCopy'
    description = u'测试Performance ArrayCopy的性能'
    path = os.path.abspath('testsuite_performace_arraycopy.html')
    level = logging.INFO # 输入日记的多少, DEBUG时最多 INFO/ERROR/CRITICAL
    verbosity = 0 # 命令行窗口的输出详细程度 0/1/2 从少到多 设定为2时可以调试一些非测试案例出错的情况

    testresult = api_unittest.htmlunittest(testsuite, title, description, path, level, verbosity)
    webbrowser.open('file:'+urllib.pathname2url(path))

#----------------------------------------------------------------------------
if __name__ == '__main__':
    main()

