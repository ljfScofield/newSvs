#!/usr/env python
# -*- coding: utf-8 -*-

""" API related with TLV string.

The module provides classes and functions to handle TLV.

__author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
__date__ = "Aug 2015"
__version__ = "0.1.0"

Copyright 2015 XH Smart Card Co,.Ltd

Author: wg@china-xinghan.com
"""

import StringIO, logging, unittest
from hubarcode.code128 import Code128Encoder
from hubarcode.ean13 import EAN13Encoder
import wx
from PIL import Image

#-------------------------------------------------------------------------------
# https://wiki.wxpython.org/WorkingWithImages

def PilImageToWxImage( myPilImage ):
    myWxImage = wx.EmptyImage( myPilImage.size[0], myPilImage.size[1] )
    myWxImage.SetData( myPilImage.convert( 'RGB' ).tobytes() )
    return myWxImage

def WxImageToWxBitmap( myWxImage ) :
    return myWxImage.ConvertToBitmap()

def PilImageToWxBitmap( myPilImage ) :
    return WxImageToWxBitmap( PilImageToWxImage( myPilImage ) )

code128_default_options = {
        'show_label' : False,
        }
ean13_default_options = {
        'show_label' : True,
        }

def resize(pilimage, codec):
    if codec=='CODE128':
        size = (405, 57)
    elif codec=='EAN13':
        size = (185, 65)
    else:
        size = (185, 65)
    pilimage.thumbnail(size, Image.BICUBIC)
    return pilimage

def generate(codec, text, bar_width=3, options=code128_default_options):
    ''' 生成条码

        codec: 'ean13', 'code128'等
        text: 文本串
        bar_width:
        options:

        返回一个wx.Bitmap
    '''
    n = codec.upper()
    if n == 'CODE128':
        enc = Code128Encoder(text, options=options) # (176, 528) to (57, 405)
    elif n== 'EAN13':
        enc = EAN13Encoder(text) # (169, 339) to (65, 185)
    else:
        raise ValueError('%s not yet supported' % codec)

    pilimage = resize(enc.get_pilimage(bar_width), codec)
    return PilImageToWxBitmap(pilimage)

#-------------------------------------------------------------------------------
class TestModule(unittest.TestCase):
    ''' 本模块的单元测试 '''

    def test_generate(self):
        with open('code128.png', 'wb') as fp:
            options = {'show_label' : False}
            raw, w, h = generate('code128', '8952020516692000313', options=options)
            fp.write(raw)
            self.assertTrue(len(raw)==528)
            self.assertTrue(w==528)
            self.assertTrue(h==176)
        with open('code128.bmp', 'wb') as fp:
            options = {'show_label' : False}
            raw, w, h = generate('code128', '8952020516692000313', options=options)
            fp.write(raw)
            self.assertTrue(len(raw)==94006)
            self.assertTrue(w==528)
            self.assertTrue(h==176)

        with open('code128_label.png', 'wb') as fp:
            options = {'show_label' : True}
            raw, w, h = generate('code128', '8952020516692000313', options=options)
            fp.write(raw)
            self.assertTrue(len(raw)==723)
            self.assertTrue(w==528)
            self.assertTrue(h==176)
        with open('code128_label.bmp', 'wb') as fp:
            options = {'show_label' : True}
            raw, w, h = generate('code128', '8952020516692000313', options=options)
            fp.write(raw)
            self.assertTrue(len(raw)==94006)
            self.assertTrue(w==528)
            self.assertTrue(h==176)

        with open('ean13.bmp', 'wb') as fp:
            raw, w, h = generate('ean13', '123456789012')
            fp.write(raw)
            self.assertTrue(len(raw)==58538)
            self.assertTrue(w==339)
            self.assertTrue(h==169)
        with open('ean13.png', 'wb') as fp:
            raw, w, h = generate('ean13', '123456789012')
            fp.write(raw)
            self.assertTrue(len(raw)==706)
            self.assertTrue(w==339)
            self.assertTrue(h==169)


#-------------------------------------------------------------------------------
if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    unittest.main()

