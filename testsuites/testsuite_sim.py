#!/usr/env python
# -*- coding: utf-8 -*-

import string, collections
import api_pcsc
import api_util
import api_unittest


#----------------------------------------------------------------------------
def isallhexdigits(s):
    ''' '0123456789abcdefABCDEF' '''
    return all([c in string.hexdigits for c in s])

ALLOWED = string.digits + string.letters +'_'


def findseperator(line):
    seps = filter(lambda x:not x in ALLOWED, line)
    return collections.Counter(seps).most_common(1)[0][0]

def isallhexdigits(s):
    ''' '0123456789abcdefABCDEF' '''
    return all([c in string.hexdigits for c in s])

def isalldigits(s):
    ''' '0123456789' '''
    return all([c in string.digits for c in s])
    
#----------------------------------------------------------------------------
class ExcelInputData(object):
    ''' 该类代表了Excel形式的输入数据，内容类似以下例子：
        ICCID/IMSI/PIN1/PUK1/PIN2/PUK2/ADM1/KI/ACC1/OPC/IMSI_ASCII/KIC1/KID1/KIK1/SYSPIN/PRINT_ICCID/PRINT_PIN1/PRINT_PUK1/PRINT_MSISDN/PRINT_HLR/PRINT_REGION
        982520506196020013F3 3943204046870774 31313131FFFFFFFF 3139323430353331 33333231FFFFFFFF 3532363637383038 4639434232423144 BB79BA6BA9C0D4E1F752640A64E4B0EA 0080 1855F4B4CEEA5D4BB2C127CBFE4EB02C 333334303230343634373837303437 1E641C0662584BE875228A3D7E2434D5 C6BF0027ED589997D4267AE0AFB8C955 31DF263E1535159FE4C2C5610AF2CA31 12BD8DBBC3DD2652 8952020516692000313F 1111 19240531 051669200031 H6 R9
        982520506196020023F1 3943204046870784 31313131FFFFFFFF 3530373435333231 35333939FFFFFFFF 3339343335303332 3033373935313432 5B5F349E113DB4EC0AC9190E8B8F80E2 0100 CAB9BB7F4002B468F39CB9EFE79C62D2 333334303230343634373837303438 8D85A0983B032B51CB0653B80F1AF47B 891B4297A0C06B64A1670CF10193C51B 64378ADD70A784C30D3FC58D0B3F14DB 72251CE007F2694D 8952020516692000321F 1111 50745321 051669200032 H6 R9
        982520506196020033F9 3943204046870794 31313131FFFFFFFF 3731313938373230 36343535FFFFFFFF 3533313835373133 3832423930323638 96D4000B85B9ECB16641E6EFC4D5175D 0200 BA18D73B314150C02E074724411B69B6 333334303230343634373837303439 4A258F03167CD4CA11DB00681132E383 5C376818FC8999DF9D51439A929A68BE 920B79BFB75BDD64FEADC9FEF1368549 1F5E4B53F08A3DB2 8952020516692000339F 1111 71198720 051669200033 H6 R9
        982520506196020043F7 3943204046870705 31313131FFFFFFFF 3838393437383639 32393735FFFFFFFF 3038323235393531 4243363334394531 FB88811C7B138B053C88A802F7E2C9AB 0001 26491E4FD51795AB89F6191B964FF9ED 333334303230343634373837303530 8B9EADBF71B6FEB92C7AEC1E945C4D28 DF9F80EFDEEB589A992B42FB46482EAD E8BEEC7735C72DA18840334365834BD6 6181D2B4013C13E3 8952020516692000347F 1111 88947869 051669200034 H6 R9
        982520506196020053F4 3943204046870715 31313131FFFFFFFF 3638353936333131 31353038FFFFFFFF 3630393935383438 3639354432334339 F16D7A3F018D7C96B7E603FB6C14ACC8 0002 1C489FAFE39904AF12D9DD72AAFCFAE6 333334303230343634373837303531 C5FE08EC54E4EACD8A0362E424787310 1EFB8E719EBD96DAF70F201F23DD49E3 2A71112AA025C41F37C2B156E9B1E502 9881CCB39DB96C08 8952020516692000354F 1111 68596311 051669200035 H6 R9
        
    '''

    def __init__(self, path):
        ''' 智能分析此类文件，得到key值列表，完成data行的格式确认

            目前只支持长度为1的分隔符
        '''
        if not os.path.isfile(path):
            raise ValueError('%s : not a valid InputData file' % path)
        fp = open(path, 'rb')
        headers = fp.readline().strip()
        #sep1 = findseperator(headers)
        sep1 = '/'
        datas = fp.readline().strip()
        #sep2 = findseperator(datas)
        sep2 = ' '
        if (not headers) or (not sep1) or (not datas) or (not sep2): # 如果这四者任意之一不正常
            raise ValueError('%s : not a valid InputData file' % path)
        hlst, dlst = headers.split(sep1), datas.split(sep2)
        m, n = len(hlst), len(dlst)
        if m != n:
            raise ValueError('%s : not a valid InputData file' % path)
        for line in fp:
            l = line.strip()
            if l:
                if len(line.split(sep2)) != n:
                    raise ValueError('%s : not a valid InputData file' % path)

        h1, d1 = sep1.join(hlst), sep2.join(dlst)
        if not h1==headers:
            raise ValueError("数据header的首尾、间隔有 %d 个多余字符" % (len(headers)-len(h1)))
        if not d1==datas:
            raise ValueError("数据的首尾、间隔有 %d 个多余字符" % (len(datas)-len(d1)))

        self.hlst, self.sep1, self.sep2 = hlst, sep1, sep2
        self.path = path
        fp.close()

    def find(self, keyword, value):
        ''' 在文件中查找以keyword-value匹配的行，以字典形式返回 '''
        i = self.hlst.index(keyword)
        with open(self.path, 'rb') as fp:
            headers = fp.readline()
            for line in fp:
                if line:
                    dlst = line.strip().split(self.sep2)
                    if dlst[i]==value:
                        return collections.OrderedDict(zip(self.hlst, dlst))
        raise ValueError('%s : %s not found in %s' %(keyword, value, self.path))

        
class TestCase_simcardtest(api_unittest.TestCase):
    ''' javacard.security.DESKey  8 type mode of paddingMode and 3 type security key        
    '''
    @classmethod
    def setUpClass(cls):
        api_pcsc.connectreader()
        path = api_unittest.getcappath('TCM51806.prd')
        excel = ExcelInputData(path)
        cls.datas = excel('ICCID', '982520506196020013F3')

    def setUp(self):
        pass

    def test_iccid(self):
		pass
