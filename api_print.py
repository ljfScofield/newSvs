#!/usr/env python
# -*- coding: utf-8 -*-

"""
    该模块提供在指定坐标绘制文本、条形码的功能，可用于绘制预期的打印版面
    This module implements a python class to draw texts & barcodes at specified positions。


    使用方法，请参考提供的模板 temple_test_print.py。
    For usage please see the provided temple_test_print.py.

    __author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
    __date__ = "Aug 2016"
    __version__ = "0.1.0"

    Copyright 2016 XH Smart Card Co,. Ltd

    Author: wg@china-xinghan.com
"""
import logging
import api_util


#----------------------------------------------------------------------------
u = api_util.u


#----------------------------------------------------------------------------
class VisualCard(object):
    ''' 代理模式，通过该类可以调用Printer的settexts(), setbarcodes()方法 '''

    def __init__(self, printer):
        ''' printer: 一个支持settexts(), setbarcodes()方法的UI控件 '''
        self.logger = logging.getLogger(self.__class__.__name__)
        self.printer = printer

    def settexts(self, texts):
        ''' texts: 一个列表，每个元素长度为2，分别为text和position，即要绘制的文本值和位置 '''
        self.printer.settexts(texts)
        return self # for chain operations

    def setbarcodes(self, barcodes):
        ''' barcodes: 一个列表，每个元素长度为2，分别为barcode和position，即要绘制的条形码值和位置 '''
        self.printer.setbarcodes(barcodes)
        return self # for chain operations

    def info(self, msg, *args, **kwargs):
        self.logger.info(u(msg), *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(u(msg), *args, **kwargs)


#----------------------------------------------------------------------------
if __name__ == '__main__':
    pass

