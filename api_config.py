#!/usr/env python
# -*- coding: utf-8 -*-

""" API related with inputdata.

The module provides utility functions for convinence.

__author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
__date__ = "Aug 2016"
__version__ = "0.1.0"

Copyright 2016 XH Smart Card Co,. Ltd

Author: wg@china-xinghan.com
"""

import logging, os, ConfigParser, re

PATH = r'.\config.ini'

CONFIG = ConfigParser.RawConfigParser(allow_no_value=True)
CONFIG.read(PATH)

def self_test():
    abspath = os.path.abspath(PATH)
    if os.path.exists(abspath):
        for x in ('__main__', 'api_pcsc', 'api_util', 'api_unittest', 'mysql'):
            if not x in CONFIG.sections():
                logging.error("Cannot find the 'main' section in configuration file: %s" % abspath)
    else:
        logging.error('Cannot find the default configuration file: %s' % abspath)

def test_exe_path():
    # test if path to svs.exe contains special characters && chinese
    # For html url, we don't want to get into the trouble of handling non-english characters
    p = os.path.abspath(os.getcwd())
    r = re.compile(r'^[0-9a-zA-Z-_.\\:]+$')
    m = r.match(p)
    if m:
        return True
    else:
        logging.error('Please DO NOT place svs.exe in non-english path: %s' % p)
        return False

def set_default_pcsc_reader_name(name):
    CONFIG.set('api_pcsc', 'defaultreadername', name) # this setting will not be saved to .ini file.

def get_default_pcsc_reader_name():
    return CONFIG.get('api_pcsc', 'defaultreadername')
    
      
def get_mysql_params():
    '''Returns IP, username, password, db name'''
    return [CONFIG.get('mysql', x) for x in ('ip', 'username', 'password', 'db')]

Datas = []
Keys = []
#dicts = {}

def set_mysql_datas(datas):
    global Datas
    Datas = datas
    
    
def set_mysql_keys(keys):
    global Keys
    Keys = keys
   
def get_mysql_dict():
    global Datas
    global Keys
    #global dicts
    dicts = dict(zip(Keys, Datas))    
    return dicts
   
    
self_test()
    

################################################################################
if __name__=='__main__':
    self_test()
     

