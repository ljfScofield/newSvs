#!/usr/env python
# -*- coding: utf-8 -*-

""" API related with PCSC.

The module provides classes and functions to access smartcards and readers.

__author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
__date__ = "Aug 2016"
__version__ = "0.1.0"

Copyright 2016 XH Smart Card Co,. Ltd

Author: wg@china-xinghan.com
"""

import binascii, time, logging, unittest
import smartcard
import smartcard.scard
import api_util
import api_config

#-------------------------------------------------------------------------------
# import utility
toBytes = api_util.toBytes
a2b = api_util.a2b
b2a = api_util.b2a

def a2blist(lst) :
    ''' Join all elements in lst and transfer to binary format.
    '''
    try:
        b = ''.join([a2b(x) for x in lst])
    except TypeError, e:
        raise PCSCException(str(x) +str(e))

    return b


def tohexstring(lst) :
    ''' Transfer a list of integer to a string, for example: tohexstring([0x3F, 0x00]) = '3F00'
    '''
    s = ''.join(map(lambda x:'%.2X'%x, lst))
    return s

#-------------------------------------------------------------------------------
# define own Exception class

class PCSCException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


#-------------------------------------------------------------------------------
# define global variable
Logger = logging.getLogger(__name__)

autoGetResponse = api_config.CONFIG.getboolean(__name__, 'autogetresponse')
stopOnError = api_config.CONFIG.getboolean(__name__, 'stoponerror')

CONNECTION = None # the reader conncection, use for all operation on smartcard

ditLastAPDU = {
    'cla' : '',
    'ins' : '',
    'p1' : '',
    'p2' : '',
    'p3' : '',
    'data' : '',
    'lc' : '',
    'le' : '',
    'response' : '',
    'sw1' : '',
    'sw2' : '',
    'sw' : '',
    'expectSW' : '',
    'expectData' : '',
    'info' : '',
    'name' : '',
    'apdu' : '',
    'time' : 0,
        }

def getconnection():
    return CONNECTION

def setconnection(x):
    global CONNECTION
    CONNECTION = x

def setlastapdu(dit):
    global ditLastAPDU
    ditLastAPDU = dit

def getlastapdu(dit):
    return ditLastAPDU


#-------------------------------------------------------------------------------
# define API

def getreaderlist():
    ''' Get the list of reader
        Returns a list, for example, ['OMNIKEY CardMan 5x21 0', 'OMNIKEY CardMan 5x21-CL 0']
    '''
    return smartcard.System.readers()


def disconnect(cold=True):
    ''' disconnect with the card
    '''
    disposition = smartcard.scard.SCARD_UNPOWER_CARD if cold else smartcard.scard.SCARD_RESET_CARD

    conn = getconnection()
    if conn:
        conn.disposition = disposition
        conn.disconnect()
        # Exception AttributeError: AttributeError("'NoneType' object has no attribute 'se
        # tChanged'",) in <bound method PCSCCardConnection.__del__ of <smartcard.pcsc.PCSC
        # CardConnection.PCSCCardConnection instance at 0x026369E0>> ignored
        #conn = None
        setconnection(None)
    else:
        pass

    return


def getatr():
    ''' returns ATR as hexdigits string '''
    conn = getconnection()
    if conn:
        return ''.join(['%.2X'%x for x in conn.getATR()]) if conn else ''
    else:
        raise PCSCException('No existed connection! Please connect reader!')


def connectreader(name='', cold=True):
    ''' Connect the specific reader.
        name:   string, reader name, example: 'OMNIKEY CardMan 5x21 0'. If not given, try to
                connect anyone avaiable.
    '''
    name = name if name else api_config.get_default_pcsc_reader_name()
    disposition = smartcard.scard.SCARD_UNPOWER_CARD if cold else smartcard.scard.SCARD_RESET_CARD
    conn = None
    if name:
        for x in smartcard.System.readers():
            if str(x) == name:
                try:
                    conn = x.createConnection()
                    conn.connect(disposition=disposition)
                except Exception as e:
                    raise PCSCException(str(e))
                break # if connected
    else: # not specified, so instead we try to connect anyone avaiable
        for x in smartcard.System.readers():
            try:
                conn = x.createConnection()
                conn.connect(disposition=disposition)
            except smartcard.Exceptions.NoCardException, e:
                continue
            except smartcard.Exceptions.CardConnectionException, e:
                continue
            except Exception as e:
                raise PCSCException(str(e))
            break # if connected

    setconnection( conn )
    if not conn:
        raise PCSCException('Smartcard not found! Please check if already inserted!')


def reset(cold=True):
    ''' Reset the card, actually combines a 'disconnect' & a 'connect' operation.
    '''
    conn = getconnection()
    disposition = smartcard.scard.SCARD_UNPOWER_CARD if cold else smartcard.scard.SCARD_RESET_CARD

    if conn:
        conn.disposition = disposition
        conn.disconnect()
        conn.connect(disposition=disposition)
        Logger.debug('reset smart card reader, ' + getatr())
    else:
        raise PCSCException('No existed connection! Please connect reader!')
    return getatr()


def is61xx(sw, expectSW):
    return (expectSW=='9000' and sw[:2]=='61')


def formatlog(apdu, response, sw1, sw2, t, name='', info=''):
    h, d = apdu[:10], apdu[10:]
    cmd = h+' '+d if d else h
    if response:
        return '%s [%s](%.2X%.2X) ; %s, %s, %.3f ms' %(cmd, response, sw1, sw2, name, info, t)
    else:
        return '%s(%.2X%.2X) ; %s, %s, %.3f ms' %(cmd, sw1, sw2, name, info, t)


def send(apdu, expectData='', expectSW='', info='', name=''):
    ''' A shortcut to 'send7816()', designed for user convinence.

        apdu: string, like '0084000004'
        expectData: string, like '01020304', can be empty
        expectSW: string, like '9000', can be empty
        info: string, just for display, can be empty
        name: string, name of APDU

        Returns response data as a string, may be empty(SW not included).
    '''
    lst = [apdu, expectData, expectSW]
    b = a2blist( lst ) # check format
    if len(apdu) < 10:
        raise PCSCException( 'Invalid APDU length %d!\n %s' %(len(apdu), apdu) )
    else:
        header = apdu[:10]
        tail = apdu[10:]
        lgth = int(header[-2:],16) *2
        if len(tail) != 0:
            if(len(tail) != lgth) and(len(tail) !=(lgth+2)): # 'Le' may be existed
                raise PCSCException( 'Invalid APDU length %d!\n %s' %(len(apdu), apdu) )


    conn = getconnection()
    t0 = time.clock()
    res, sw1, sw2 = conn.transmit( toBytes(apdu) )

    t1 = time.clock()
    t =(t1-t0)*1000

    if autoGetResponse:
        if sw1==0x61 and sw2 != 0x00:
            apdu1 = '00C00000%.2X' % sw2
            btes = toBytes(apdu1)
            res, sw1, sw2 = conn.transmit( btes )
        if sw1==0x6C and sw2 != 0x00:
            apdu1 = '%s%.2X' %(apdu[:8], sw2)
            btes = toBytes(apdu1)
            res, sw1, sw2 = conn.transmit( btes )


    response = tohexstring( res )
    sw = '%.2X%.2X'%(sw1, sw2)

    Logger.debug(formatlog(apdu, response, sw1, sw2, t, name, info))

    dit = {
            'cla' : apdu[:2],
            'ins' : apdu[2:4],
            'p1' : apdu[4:6],
            'p2' : apdu[6:8],
            'p3' : apdu[8:10],
            'data' : apdu[10:10+lgth],
            'lc' : apdu[8:10],
            'le' : apdu[10+lgth:],
            'response' : response,
            'sw1' : '%.2X'%sw1,
            'sw2' : '%.2X'%sw2,
            'sw' : sw,
            'expectData' : expectData,
            'expectSW' : expectSW,
            'info' : info,
            'name' : name,
            'apdu' : apdu,
            'time' : t,
            }

    setlastapdu( dit )

    # check sw
    if expectSW:
        if sw!=expectSW and stopOnError:
            if not is61xx(sw, expectSW):
                raise PCSCException('Error! Unexpected status words(%s) returned by card:\n%s, %s,(%s)' %(sw, name, info, expectSW))

    # check response
    if expectData:
        if response!=expectData and stopOnError:
            raise PCSCException('Error! Unexpected response-data returned by card:\n%s\n%s, %s, [%s]' %(response, name, info, expectData))

    # log information
    if info:
        #LogMessage(info)
        pass

    return response, sw


def send7816(cla, ins, p1, p2, p3, data='', le='', expectData='',  expectSW='', info='', name=''):
    ''' Send any apdu to smartcard connected via T0/T1 protocol.
        P3 will be automaticlly caculated and appended.

        cla: string, like 'A0'
        ins: string, like 'A4'
        p1:  string, like '00'
        p2:  string, like '00'
        p3:  string, like '02'
        data: string, like '3F00', will be sent to smartcard.
        le: string, like '00'
        expectData: string, like '6F0E8408A000000333CDD000A5028800', can be empty.
        expectSW: string, like '9F17', can be empty.
        info: string, just for display
        name: string, APDU name

        Returns 'Data response' + SW, data may be an empty string.
    '''
    
    lst = [cla, ins, p1, p2, p3]
    b = a2blist( lst ) # check format
    apdu = ''.join( lst )
    if len(apdu) != 10:
        raise PCSCException( 'Invalid APDU length %d! MUST be 10!\n %s' %(len(apdu), apdu) )

    lst = [data, expectSW, expectData]
    b = a2blist( lst ) # check format

    if data:
        lgth = int(p3, 16)*2
        if(lgth != len(data)) and((lgth+2) != len(data)):
            raise PCSCException( "Invalid APDU: 'P3'(0x%s, %d) does not mathch with the length of 'Data'(%d)"
                    %(p3, lgth, len(data)) )
    apdu += data # add 'Data'

    if le:
        try:
            a2b(le) # check format
        except TypeError, e:
            raise PCSCException( "Invalid 'LE' : %s\n%s" %(le, str(e)) )

        apdu += le # add 'Le'

    return send(apdu, expectData=expectData, expectSW=expectSW, info=info, name=name)


def getexectime():
    ''' Get the execution time of last apdu.
    '''
    return ditLastAPDU['time']


def setautogetresponse(flag):
    ''' Set if auto 'Get Response' when '61XX' received.
    '''
    global autoGetResponse
    autoGetResponse = flag
    return

#----------------------------------------------------------------------------
class TestModule(unittest.TestCase):
    ''' 本模块的单元测试 '''

    def test_00A4(self):
        for x in range(10):
            connectreader(cold=True)
            r, sw = send('00A4040000')
            assert type(r) == type('')
            assert sw == '9000'
            disconnect(cold=True)

            connectreader(cold=True)
            r, sw = send('00A4040000')
            assert type(r) == type('')
            assert sw == '9000'
            disconnect(cold=False)



#-------------------------------------------------------------------------------
if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    unittest.main()

