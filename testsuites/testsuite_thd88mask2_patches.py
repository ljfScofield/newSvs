#!/usr/env python
# -*- coding: utf-8 -*-

""" 验证THD88maskv2的3个补丁：timer没有正确关闭导致的pps间隔问题、EDEP converter、license disable

This script will check if THD88maskv2 already fixed all known OS bugs.

__author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
__date__ = "Feb 2017"
__version__ = "0.1.0"

Copyright 2017 XH Smart Card Co,. Ltd

Author: wg@china-xinghan.com
"""

import logging, os, webbrowser, unittest, urllib

import api_pcsc
import api_gp
import api_util
import api_unittest


#----------------------------------------------------------------------------
u = api_util.u

class TestCase_THD88maskve_Patches(api_unittest.TestCase):
    ''' 验证THD88maskv2的3个OS补丁：timer没有正确关闭导致的pps间隔问题、EDEP converter、license disable
    '''

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_timer_pps(self):
		self.fail('TODO')
		
    def test_edep_converter(self):
		self.fail('TODO')
		
    def test_license_disabled(self):
		self.fail('TODO')
		
#----------------------------------------------------------------------------
def main():
    classes = (
        TestCase_THD88maskve_Patches,
        )
    testsuite = unittest.TestSuite([api_unittest.TestLoader().loadTestsFromTestCase(clz) for clz in classes])
    title = u'ETC ITS BCTC'
    description = u'验证THD88maskv2的3个OS补丁：timer没有正确关闭导致的pps间隔问题、EDEP converter、license disable'
    path = os.path.abspath('testsuite_thd88mask2_patches.html')
    level = logging.INFO # 输入日记的多少, DEBUG时最多 INFO/ERROR/CRITICAL
    verbosity = 0 # 命令行窗口的输出详细程度 0/1/2 从少到多 设定为2时可以调试一些非测试案例出错的情况

    testresult = api_unittest.htmlunittest(testsuite, title, description, path, level, verbosity)
    webbrowser.open('file:'+urllib.pathname2url(path))

#----------------------------------------------------------------------------
if __name__ == '__main__':
    main()

