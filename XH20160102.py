#!/usr/env python
# -*- coding: utf-8 -*-

""" 检测XH20160102号订单

This script will check if our XH20160102 product compliants with customer requirment.

__author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
__date__ = "Aug 2016"
__version__ = "0.1.0"

Copyright 2016 XH Smart Card Co,. Ltd

Author: wg@china-xinghan.com
"""

import logging
import api_inputdata
import api_util
import api_validators
import api_print
import api_incarddata

#-------------------------------------------------------------------------------
u = api_util.u
ExcelInputData = api_inputdata.ExcelInputData
InputDataValidator = api_inputdata.InputDataValidator
VisualCard = api_print.VisualCard
UsimDataValidator = api_incarddata.UsimDataValidator

logger = logging.getLogger(__name__)


#-------------------------------------------------------------------------------
class PIN1(api_validators.PIN1Validator):

    KEY = 'PIN1'

    def dotest(self, datas):
        ''' 检查PIN值是否为固定值 31313131FFFFFFFF
        '''
        k, v = self.getkv(datas)
        self.assertTrue(v=='31313131FFFFFFFF', '%s: %s 不是客户指定的固定值 1111' % (k,v))

class PRINT_MSISDN(api_validators.PIN1Validator):

    KEY = 'PRINT_MSISDN'

    def dotest(self, datas):
        ''' 检查PRINT_MSISDN值是否为ICCID末尾12个字符 
        '''
        k, v = self.getkv(datas)
        iccid = api_util.swap(datas['ICCID'])[:-1]
        self.assertTrue(v==iccid[-12:], '%s: %s 不是ICCID末尾12个字符 %s ' % (k,v, iccid[-12:]))


#-------------------------------------------------------------------------------
def test_XH20160102(order, inppath, iccid, printer):
    ''' 测试XH20160102号订单

        order: 订单号
        inppath: .prd输入数据文件的路径
        iccid: 
        printer: 测试软件提供的虚拟打印机，用于打印文本、条形码到虚拟卡面

        检测结束后返回3个值：正确个数、警告个数、错误个数
        错误个数为0时认为检测通过
    '''
    # 1. 测试prd输入数据
    datas = ExcelInputData(inppath).find('ICCID', iccid)
    telcel_vs = {'PIN1' : PIN1(), 'PRINT_MSISDN' : PRINT_MSISDN(), }   # telcel某些数据有特殊要求，比如PIN1固定为1111
    r1 = InputDataValidator().test(datas, telcel_vs)

    # 2. 打印版面：文本、条形码
    w, h = printer.getwidthheight()
    x, y = printer.getsmallcardposition()
    w1, h1 = printer.getsmallcardwidthheight()
    telcel_texts = [
            ('PIN1: '+datas['PRINT_PIN1'] + '    PUK1: '+datas['PRINT_PUK1'], (w*0.5, h*0.1)),
            (datas['PRINT_ICCID'][:10], (x+w1*0.3, y+h1*0.1)),
            (datas['PRINT_HLR'],        (x+w1*0.6, y+h1*0.3)),
            (datas['PRINT_ICCID'][10:], (x+w1*0.3, y+h1*0.6)),
            (datas['PRINT_ICCID'][:-1] +'  '+ datas['PRINT_HLR'] +' '+ datas['PRINT_REGION'], (w*0.1, h*0.9)),
            ]
    barcodes = [
            # 内容、位置、编码格式
            (datas['PRINT_ICCID'][:-1], (w*0.1, h*0.6), 'CODE128'),
            ]
    visual = VisualCard(printer)
    visual.settexts(telcel_texts).setbarcodes(barcodes)

    # 3. 卡内个性化数据
    # 3.1 USIM
    datas['ATR'] = '3B9E94801F478031A073BE21106686880212204027'
    r2 = UsimDataValidator().test(datas)

    # 4. 文件系统 
    pass

    # 4. 特殊应用
    pass

    # 6. 结束
    passedno1, warningno1, errorno1 = 0, 0, 0
    for t, numbers in (('1. 输入数据校验', r1), ('2. 卡内数据校验', r2), ):
        passedno, warningno, errorno = numbers
        msg = u('%s：%d 项通过, %d 项警告, %d 项错误' % (t, passedno, warningno, errorno))
        if warningno or errorno: # 有警告或错误
            logger.error(msg)
        else:
            logger.info(msg)
        passedno1 += passedno
        warningno1+= warningno
        errorno1  += errorno
    return passedno1, warningno1, errorno1

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)

    order = 'XH20160102'
    inppath = r'F:\XHSVS\XHSVSClient\testscript\XH_RF_P3TELMX_EP6.3_P11R10V12_1.OS_SAMSNG_S3FS9FV_JAVA_3G_CAT_HTTP_BRS_SAT_R263\INP\TCM51806.prd'
    iccid = '982520506196020013F3'
    test_XH20160102(order, inppath, iccid)

