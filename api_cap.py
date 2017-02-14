#!/usr/env python
# -*- coding: utf8 -*-

""" APIs handle with Java Card's CAP file.


__author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
__date__ = "Aug 2015"
__version__ = "0.1.0"

Copyright 2015 XH Smart Card Co,.Ltd

Author: atr@china-xinghan.com
"""

import binascii, time, os, zipfile, re, unittest


b2a = binascii.b2a_hex
a2b = binascii.a2b_hex

dit_known_pkg = {
    'A0000000620001': r'java/lang',
    'A0000000620101': r'javacard/framework',
    'A0000000620102': r'javacard/security',
    'A0000000620201': r'javacardx/crypto',
    }


list_component = [ # TABLE 6-2  CAP File Component File Names, 12 kinds
    'Header',
    'Directory',
    'Applet', # 3, optional
    'Import',
    'ConstantPool',
    'Class',
    'Method',
    'StaticField',
    'RefLocation',
    'Export', # 10, optional
    'Descriptor',
    'Debug' # 12, optional
    ]


pat_u1 = '\w{2}' # regular expression, 2-hexdigits of 'u1'
pat_u1not0 = '(?!00)\w{2}' # regular expression, 2-hexdigits of 'u1' but not '00' allowed

pat_u2 = '\w{4}' # regular expression, 4-hexdigits of 'u2'
pat_u2not0 = '(?!0000)\w{4}' # regular expression, 4-hexdigits of 'u2' but not '0000' allowed


def sliceHex(s, width, extra='[\w]*'):
    ''' Slice a string according to the width

         s: ascii string, like '11aabbAABBCC'
         width: a tuple, like (1,2,3)
         extra: indicate the patter of extra fields

         sliceHex('11aabbAABBCC', (1,2,3)) will return ('11', 'aabb', 'AABBCC')
    '''
    lst = ['([\w]{%d})'%(w*2) for w in width]

    if extra:
        lst.append('(%s)'%extra) # for extra characters

    pattern = ''.join(lst)

    lst = re.findall(pattern, s)

    if lst:
        return lst[0]
    else:
        raise ValueError('No enough fields for slice operation')



class TLV(object):
    '''
    '''
    def __init__(self, tlv, width=(1,1)):
        ''' class of 'TLV object'

             tlv: hex-digit string, like '80020102'
             width: a tuple, indicate the width of 'Tag' & 'Length' fields.
        '''
        a2b(tlv) # check if all hex-digit & even length

        self.tlv = tlv.upper()

        if len(tlv) < sum(width)*2:
            raise ValueError("Too short: No enough fields for 'Tag' & 'Length'")
        else:
            L1 = width[0] * 2
            L2 = width[1] * 2

            self.tag = self.tlv[:L1]
            self.length = self.tlv[L1:(L1+L2)]

            L3 = int(self.length, 16) * 2

            if len(self.tlv[(L1+L2):]) < L3:
                raise ValueError("Too short: No enough fields for 'Value'")
            else:
                self.value = self.tlv[(L1+L2):(L1+L2+L3)]
                self.extra = self.tlv[(L1+L2+L3):] # normally 'extra' is an empty string

            # setup alias (another name)
            self.t = self.tag
            self.l = self.length
            self.v = self.value
            self.size = L3


    def __str__(self):
        return '%s%s%s' % (self.tag, self.length, self.value)

#-------------------------------------------------------------------------------
class CAPException(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

#-------------------------------------------------------------------------------
class Component(object):
    ''' Abstract class of 'Commponent' in CAP File .

         see Chapter 6.1 Component Model, JCVM spec
    '''

    def __init__(self, data):
        ''' data: a string, example: '010011DECAFFED010204000107A000000333CDD0'

                header_component {
                u1 tag
                u2 size
                }
        '''
        self.items_name = ('tag', 'size')
        self.pattern = '%s%s'%(pat_u1, pat_u2not0)

        self.tlv = TLV(data, width=(1,2))
        self.tag = self.tlv.t
        self.size = self.tlv.length
        self.items = dict(zip(self.items_name, (self.tag, self.size)))


    def __str__(self):
        return str(self.tlv)


    def dump(self):
        ''' Dump all fields and return details.

             returns a multi-line string, one filed a line.
        '''
        # 'Name: Value'
        return ''.join(['%s: %s\n'%(x, self.items[x]) for x in self.items_name])


    def comment(self):
        ''' Returns helpful comments on some complicate items
        '''
        return ''


    def selfcheck(self, pattern=None):
        ''' Check if 'Component' compatibility with the JCVM spec.

             returns True or False
        '''
        if not pattern:
            pattern = self.pattern

        m = re.match(pattern, str(self))

        return True if m else False



class Header(Component):
    ''' Abstract class of 'Header Component' . 

         see Chapter 6.3 Header Component, JCVM spec
    '''


    def __init__(self, data):
        ''' data: a string, example: '010011DECAFFED010204000107A000000333CDD0'

                header_component {
                u1 tag
                u2 size
                u4 magic
                u1 minor_version
                u1 major_version
                u1 flags
                package_info package
                # package_name_info package_name # omit this item, no meaningful in Java Card
                }
        '''
        Component.__init__(self, data)

        self.items_name = (
                'tag',
                'size',
                'magic',
                'minor_version',
                'major_version',
                'flags',
                'package_info_minor_version',
                'package_info_major_version',
                'package_info_AID_length',
                'package_info_AID',
                'package_name_info_name_length',
                'package_name_info_name',
                )

        # pattern = '01(?!0000)\w{4}(DECAFFED01020|DECAFFED02020)[0-7]\d{2}\w{2,}$'
        self.pattern = '01' +pat_u2not0 +'(DECAFFED01020|DECAFFED02020)[0-7]\d{2}\w{2,}$'

        lst = sliceHex(self.tlv.v, (4,1,1,1, 1,1,1)) # from 'magic' to 'package_info_AID_length', & extra
        if lst:
            aidlgth = int(lst[-2], 16)
            extra = lst[-1]
            aid, extra = sliceHex(extra, (aidlgth,)) # 'aid'
            if not aid:
                raise CAPException("Too short: No enough fields for Header component (AID)")
            if extra:
                name_lgth = extra[:2]
                name = extra[2:]
            else:
                name_lgth = ''
                name = ''
        else:
            raise CAPException('Too short: No enough fields for Header component')

        lst_attr = [self.tag, self.size] + list(lst[:-1]) +[aid, name_lgth, name]
        self.items = dict(zip(self.items_name, lst_attr))


    def comment(self):
        ''' Returns helpful comments on some complicate items
        '''
        flags = int(self.items['flags'], 16)
        dit = {
                1: 'The Java int type is used in this package',
                2: 'An Export Component is included in this CAP file',
                4: 'An Applet Component is included in this CAP file',
                }
        return '\n'.join([dit[x] for x in dit if (flags & x) == x])



class Directory(Component):
    ''' Abstract class of 'Directory Component' . 

         see Chapter 6.4 Directory Component, JCVM spec
    '''
    def __init__(self, data):
        ''' data: a string, example: '02001F0011001F000C001E00B200540285000A004000000184000000000000030100'

            directory_component {
                u1 tag
                u2 size
                u2 component_sizes[12]
                static_field_size_info static_field_size {u2 image_size, u2 array_init_count, u2 array_init_size}
                u1 import_count
                u1 applet_count
                u1 custom_count
                custom_component_info custom_components[custom_count]
            }
        '''
        Component.__init__(self, data)

        self.items_name = (
                'tag',
                'size',
                'component_sizes',
                'image_size',
                'array_init_count',
                'array_init_size',
                'import_count',
                'applet_count',
                'custom_count',
                'custom_components',
                )

        self.pattern = '02' +pat_u2not0 +pat_u2not0*2 +pat_u2 +pat_u2not0*6 +pat_u2 +pat_u2not0 +pat_u2 +'\w{14,18}' +'\w?$'


        lst = sliceHex(self.tlv.v, (24, 2, 2)) # component_sizes image_size array_init_count, extra
        if lst:
            array_init_count = int(lst[-2], 16)
            extra = lst[-1]
            try:
                array_init_size, import_count, applet_count, custom_count, custom_components = sliceHex(extra, (2,1,1,1,))
            except ValueError as e:
                if not array_init_count:
                    array_init_size = ''
                    import_count, applet_count, custom_count, custom_components = sliceHex(extra, (1,1,1,))
                else:
                    raise CAPException(str(e))
        else:
            raise CAPException('Too short: No enough fields for Directory component')

        lst_attr = [self.tag, self.size] +list(lst[:-1]) +[array_init_size, import_count, applet_count, custom_count, custom_components]
        self.items = dict(zip(self.items_name, lst_attr))


    def comment(self):
        ''' Returns helpful comments on some complicate items
        '''
        sizes = self.items['component_sizes']
        lgth = len(sizes)
        include = [int(sizes[i:i+4], 16) for i in range(0,lgth,4)]

        lst = zip(list_component, include)
        comment = ''.join(['%s not included\n'%name for name, lgth in lst if not lgth])

        return comment



class Applet(Component):
    ''' Abstract class of 'Applet Component' . 

         see Chapter 6.5 Applet Component, JCVM spec
    '''
    def __init__(self, data):
        ''' data: a string, example: '03000C0108A000000333CDD0000141'

            applet_component {
                u1 tag
                u2 size
                u1 count
                { u1 AID_length
                  u1 AID[AID_length]
                  u2 install_method_offset
                } applets[count]
            }
        '''
        Component.__init__(self, data)

        self.items_name = (
                'tag',
                'size',
                'count',
                'applets',
                )

        self.pattern = '03' +pat_u2not0 +pat_u1not0*2 +'\w{9,}$' # 9 = 5 + 4, shortest AID & a u2


        lst = sliceHex(self.tlv.v, (1,)) # 'count', 'applets'
        if lst:
            pass
        else:
            raise CAPException('Too short: No enough fields for Applet component')

        lst_attr = [self.tag, self.size] +list(lst)
        self.items = dict(zip(self.items_name, lst_attr))


    def comment(self):
        ''' Returns helpful comments on some complicate items
        '''
        count = int(self.items['count'], 16)
        applets = self.items['applets']

        if not count:
            return  "The value of the 'count' item must be greater than zero."

        lgth = len(applets)
        if lgth<count*(1+5+2):
            return "Too short: No enough fields for 'applets' item in Applet component"

        lst = []
        while count:
            lgth = int(applets[:2], 16)
            aid = applets[2:(2+lgth*2)]
            offset = applets[(2+lgth*2):(2+lgth*2+4)]
            applets = applets[(2+lgth*2+4):]
            lst.append((lgth, aid, offset, int(offset,16)))
            count = count-1

        comment = '\n'.join([str(applet) for applet in lst])
        return comment



class Import(Component):
    ''' Abstract class of 'Import Component' . 

         see Chapter 6.6 Import Component, JCVM spec
    '''
    def __init__(self, data):
        ''' data: a string, example: '04001E03000106A000000333CD030107A0000000620101000107A0000000620001'

            import_component {
                u1 tag
                u2 size
                u1 count
                package_info packages[count]
            }
        '''
        Component.__init__(self, data)

        self.items_name = (
                'tag',
                'size',
                'count',
                'packages',
                )

        self.pattern = '04' +pat_u2not0 +pat_u1 +'\w*$' # tag, size, count, packages (optional)


        lst = sliceHex(self.tlv.v, (1,)) # 'count', 'packages'
        if lst:
            pass
        else:
            raise CAPException('Too short: No enough fields for Import component')

        lst_attr = [self.tag, self.size] +list(lst)
        self.items = dict(zip(self.items_name, lst_attr))


    def comment(self):
        ''' Returns helpful comments on some complicate items
        '''
        count = int(self.items['count'], 16)
        pkgs = self.items['packages']

        if not count:
            return  "No imported package"

        lgth = len(pkgs)
        if lgth<count*(1+1+1+5):
            return "Too short: No enough fields for 'packages' item in Import component"

        lst = []
        while count and pkgs:
            minor = pkgs[:2]
            major = pkgs[2:4]
            lgth = int(pkgs[4:6], 16)
            aid = pkgs[6:(6+lgth*2)]
            name = dit_known_pkg.get(aid, '')
            lst.append('%s v%s.%s %s'%(aid, major, minor, name))
            pkgs = pkgs[(6+lgth*2):]
            count = count-1

        comment = '\n'.join(lst)
        return comment


dit_constant_pool_tags = {
    '01': 'CONSTANT_Classref', 
    '02': 'CONSTANT_InstanceFieldref', 
    '03': 'CONSTANT_VirtualMethodref', 
    '04': 'CONSTANT_SuperMethodref', 
    '05': 'CONSTANT_StaticFieldref', 
    '06': 'CONSTANT_StaticMethodref', 
    }


class cp_info(object):
    '''
    '''
    def __init__(self, data):
        '''
        '''
        self.tag = data[:2]
        self.info = data[2:]

    def __str__(self):
        tag = self.tag
        info = self.info

        dit = {}
        dit['tag'] = dit_constant_pool_tags.get(tag, 'Unknown conatant type')

        if tag=='01': # CONSTANT_Classref
            dit['padding'] = info[4:]

            if int(info[:4], 16) > 0x7FFF: # external
                dit['package_token'] = info[:2]
                dit['class_token'] = info[2:4]
            else: # internal
                dit['class_offset'] = info[:4]
        elif tag in ['02','03','04']: # CONSTANT_InstanceFieldref CONSTANT_VirtualMethodref CONSTANT_SuperMethodref
            token = info[4:]
            dit['token'] = token

            if int(info[:4],16) > 0x7FFF: # external
                dit['package_token'] = info[:2]
                dit['class_token'] = info[2:4]
            else: # internal
                dit['class_offset'] = info[:4]
        elif tag in ['05','06']:
            if info[:2] == '00': # internal
                dit['padding'] = '00'
                dit['offset'] = info[2:]
            else:
                dit['package_token'] = info[:2]
                dit['class_token'] = info[2:4]
                dit['token'] = info[4:]
        else:
            pass

        lst = ['tag', 'package_token', 'class_token', 'class_offset', 'offset', 'token', 'padding']
        s = ', '.join(['%s: %s'%(x,dit[x]) for x in lst if x in dit])
        return s



class ConstantPool(Component):
    ''' Abstract class of 'ConstantPool Component' . 

         see Chapter 6.7 ConstantPool Component, JCVM spec
    '''
    def __init__(self, data):
        ''' data: a string, example: '0500AE002B0280000002000E0302000E0102000E0202000E00028002010280020003000E08018107000680000006810300068001000180000003800619068003000680040003810A060180030003810302060001E606000009038000010100240003800820068110010380081C06810701018008000100020001000E00040024180600003C0381070103810A080400240B068007000180040003810A010380070404000209060001C80380061406800800'

            constant_pool_component {
                u1 tag
                u2 size
                u2 count
                cp_info constant_pool[count]
            }
        '''
        Component.__init__(self, data)

        self.items_name = (
                'tag',
                'size',
                'count',
                'constant_pool',
                )

        self.pattern = '05' +pat_u2not0 +pat_u1 +'\w*$' # tag, size, count, constant_pool (optional)


        lst = sliceHex(self.tlv.v, (2,)) # 'count', 'constant_pool'
        if lst:
            pass
        else:
            raise CAPException('Too short: No enough fields for ConstantPool component')

        lst_attr = [self.tag, self.size] +list(lst)
        self.items = dict(zip(self.items_name, lst_attr))


    def comment(self):
        ''' Returns helpful comments on some complicate items
        '''
        count = int(self.items['count'], 16)
        pool = self.items['constant_pool']

        if not count:
            return  "No constant pool existed"

        lgth = len(pool)
        if lgth<count*(1+3):
            return "Too short: No enough fields for 'cp_info' item in ConstantPool component"

        step = (1+3)*2
        lst = [str(cp_info(pool[i:i+step])) for i in range(0,lgth,step)]

        comment = '%d cp_info:\n'%count + '\n'.join(lst)
        return comment



class CAPFile(object):
    ''' Abstract of 'CAP File' .
    '''
    def __init__(self, path):
        self.jar = zipfile.ZipFile(path, 'r')
        self.path = path
        self.size = os.path.getsize(path)
        self.mtime = time.strftime('%Y%m%d-%H:%M:%S', time.localtime(os.path.getmtime(path)))


    def close(self):
        ''' Close the archive file. You must call close() before exiting your program or essential records will not be written.
        '''
        self.jar.close()
        return


    def namelist(self):
        ''' Return a list of archive members by name.
        '''
        return self.jar.namelist()


    def manifest(self, name='META-INF/MANIFEST.MF'):
        ''' Return the content of META-INF/MANIFEST.MF .

             returns a dictionary (empty if manifest not found).
        '''
        if name in self.jar.namelist():
            mf = self.jar.read(name)
            return dict([line.split(': ') for line in mf.split('\r\n') if line and ': ' in line])
        else:
            return dict()

    def getPackageAID(self, tag='Java-Card-Package-AID'):
        ''' 
        '''
        mf = self.manifest()
        if tag in mf:
            aid = mf[tag]
        elif 'AID' in mf:
            aid = mf['AID']
        else:
            aid = ''

        return aid.replace('0x', '').replace(':','').upper()

    def getPackageName(self, tag='Java-Card-Package-Name'):
        ''' 
        '''
        mf = self.manifest()
        if tag in mf:
            return mf[tag]
        elif 'Name' in mf:
            return mf['Name']
        else:
            name = self.jar.namelist()[0] # 'com/company/javacard/lib_zyt/javacard/Header.cap'
            d = os.path.dirname(name) # 'com/company/javacard/lib_zyt/javacard'
            pkg = os.path.dirname(d) # 'com/company/javacard/lib_zyt/javacard'
            return pkg


    def readCap(self, name, directory=r'/javacard/', suffix='.cap'):
        ''' Return the bytes of the file name in the archive.
        '''
        pkg = self.getPackageName()
        if '.' in pkg:
            pkg = pkg.replace('.', '/')

        fullpath = pkg +directory +name +suffix


        if fullpath in self.jar.namelist():
            return b2a(self.jar.read(fullpath)).upper()
        else:
            return '%s not found in the CAP file'%fullpath


    def readAllCap(self, lst, directory=r'/javacard/', suffix='.cap'):
        ''' Return all bytes of the files in the list.
        '''
        pkg = self.getPackageName()
        if '.' in pkg:
            pkg = pkg.replace('.', '/')

        paths = [''.join([pkg, directory, f, suffix]) for f in lst]
        namelist = self.jar.namelist()
        caps = ''.join([self.jar.read(p) for p in paths if p in namelist])

        return b2a(caps).upper()


    def readManifest(self, name='META-INF/MANIFEST.MF'):
        ''' Return the bytes of the file name in the archive.

             returns a string
        '''
        try:
            return self.jar.read(name)
        except KeyError, e:
            return str(e)


dit_component_class = { # component name & class
    'Header': Header,
    'Directory':Directory,
    'Applet':Applet,
    'Import':Import,
    'ConstantPool':ConstantPool,
    }

#----------------------------------------------------------------------------
class TestModule(unittest.TestCase):
    ''' 本模块的单元测试 '''

    def test_helloworld(self):
        ''' 用D:\GPShell-1.4.4\helloworld.cap验证cap文件相关class的正确性 '''
        path = r'./helloworld.cap'

        cap = CAPFile(path)
        self.assertTrue(cap.mtime=='20101031-03:57:38')
        self.assertTrue(cap.size==2449)
        self.assertTrue(cap.readManifest()=='"There is no item named \'META-INF/MANIFEST.MF\' in the archive"')
        self.assertTrue(cap.getPackageName()=='net/sourceforge/globalplatform/jc/helloworld')

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    unittest.main()

