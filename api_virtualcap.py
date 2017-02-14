#!/usr/env python
# -*- coding: utf8 -*-

""" 虚拟CAP，用于创建各种异常字节码，以便测试JCVM的安全机制


__author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
__date__ = "Aug 2015"
__version__ = "0.1.0"

Copyright 2015 XH Smart Card Co,.Ltd

Author: atr@china-xinghan.com
"""

import struct, binascii, zipfile, re, unittest


#----------------------------------------------------------------------------
b2a = binascii.b2a_hex
a2b = binascii.a2b_hex

def getbyte(u1):
    return struct.unpack('!B', u1)[0]

def getshort(u2):
    return struct.unpack('!H', u2)[0]

def setshort(u2):
    return struct.pack('!H', u2)

#----------------------------------------------------------------------------

SEQUENCE = (
    'Header.cap',
    'Directory.cap',
    'Import.cap',
    'Applet.cap', # optional, may be not existed
    'Class.cap',
    'Method.cap',
    'StaticField.cap',
    'Export.cap',
    'ConstantPool.cap',
    'ReferenceLocation.cap',
    'Descriptor.cap', # optional
    'Debug.cap', # optional
    )


class Component(object):
    '''
        component {
            u1 tag
            u2 size
            u1 info[]
        }
    '''

    def __init__(self, tlv):
        self.tag, self.size, self.info = tlv[0], getshort(tlv[1:3]), tlv[3:]

    def __str__(self):
        return self.tag + self.size + self.info


#----------------------------------------------------------------------------
class Header(Component):
    '''
        header_component {
            u1 tag
            u2 size
            u4 magic
            u1 minor_version
            u1 major_version
            u1 flags
            package_info package
            package_name_info package_name
        }
    '''

    def __init__(self, tlv):
        Component.__init__(self, tlv)

#----------------------------------------------------------------------------
class Directory(Component):
    '''
        directory_component {
            u1 tag
            u2 size
            u2 component_sizes[12]
            static_field_size_info static_field_size
            u1 import_count
            u1 applet_count
            u1 custom_count
            custom_component_info custom_components[custom_count]
        }
    '''
    def __init__(self, tlv):
        Component.__init__(self, tlv)

#----------------------------------------------------------------------------
class Import(Component):
    '''
        import_component {
            u1 tag
            u2 size
            u1 count
            package_info packages[count]
        }
    '''
    def __init__(self, tlv):
        Component.__init__(self, tlv)

#----------------------------------------------------------------------------
class Applet(Component):
    '''
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
    def __init__(self, tlv):
        Component.__init__(self, tlv)

#----------------------------------------------------------------------------
class Clazz(Component):
    '''
        class_component {
            u1 tag
            u2 size
            u2 signature_pool_length
            type_descriptor signature_pool[]
            interface_info interfaces[]
        }
    '''
    def __init__(self, tlv):
        Component.__init__(self, tlv)


#----------------------------------------------------------------------------
class Exception_handler_info(object):
    '''
        exception_handler_info {
            u2 start_offset
            u2 bitfield {
                bit[1] stop_bit
                bit[15] active_length
            }
            u2 handler_offset
            u2 catch_type_index
        }
    '''

    def __init__(self, v):
        # The start_offset item and end_offset are byte offsets into the info item of
        # the Method Component. The value of the start_offset must be a valid offset
        # into a bytecodes array of a method_info structure to an opcode of an instruction. 
        self.start_offset = getshort(v[:2])
        bitfield = getshort(v[2:4])
        # The stop_bit item is equal to 1 if the active range does not intersect with a
        # succeeding exception handler’s active range, and this exception handler is the last
        # handler applicable to the active range
        self.stop_bit = ((bitfield>>15) &0x01)==1
        self.active_length = bitfield&0x7FFF

        # The handler_offset item represents a byte offset into the info item of the
        # Method Component. It indicates the start of the exception handler. At the Java
        # source level, this is equivalent to the beginning of a catch or finally block. 
        self.handler_offset = getshort(v[4:6])

        # If the value of the catch_type_index item is non-zero, it must be a valid index
        # into the constant_pool[] array of the Constant Pool Component (Section 6.7,
        # Constant Pool Component on page 6-14). The constant_pool[] entry at that
        # index must be a CONSTANT_Classref_info structure, representing the class of
        # the exception caught by this exception_handlers array entry.
        self.catch_type_index = getshort(v[6:8])

class Methods(Component):
    '''
        method_component {
            u1 tag
            u2 size
            u1 handler_count
            exception_handler_info exception_handlers[handler_count]
            method_info methods[]
        }
    '''
    def __init__(self, tlv):
        Component.__init__(self, tlv)
        # The start_offset item and end_offset are byte offsets into the info item of
        # the Method Component. The value of the start_offset must be a valid offset
        # into a bytecodes array of a method_info structure to an opcode of an
        # instruction. 
        exception_handlers = self.info[1:1+getbyte(self.info[0])*8]
        self.exception_handlers = [Exception_handler_info(exception_handlers[i:i+8]) for i in range(0, len(exception_handlers), 8)]
        self.methods = self.info[1+getbyte(self.info[0])*8:]

    def __str__(self):
        info = ord(len(self.exception_handlers)) + self.exception_handlers + self.methods
        return self.tag + setshort(len(info)) + info

#----------------------------------------------------------------------------
class StaticField(Component):
    '''
        static_field_component {
            u1 tag
            u2 size
            u2 image_size
            u2 reference_count
            u2 array_init_count
            array_init_info array_init[array_init_count]
            u2 default_value_count
            u2 non_default_value_count
            u1 non_default_values[non_default_values_count]
        }
    '''
    def __init__(self, tlv):
        Component.__init__(self, tlv)

#----------------------------------------------------------------------------
class Export(Component):
    '''
        export_component {
            u1 tag
            u2 size
            u1 class_count
            class_export_info {
                u2 class_offset
                u1 static_field_count
                u1 static_method_count
                u2 static_field_offsets[static_field_count]
                u2 static_method_offsets[static_method_count]
            } class_exports[class_count]
        }
    '''
    def __init__(self, tlv):
        Component.__init__(self, tlv)

#----------------------------------------------------------------------------
class ConstantPool(Component):
    '''
        constant_pool_component {
            u1 tag
            u2 size
            u2 count
            cp_info constant_pool[count]
        }
    '''
    def __init__(self, tlv):
        Component.__init__(self, tlv)

#----------------------------------------------------------------------------
class ReferenceLocation(Component):
    '''
        reference_location_component {
            u1 tag
            u2 size
            u2 byte_index_count
            u1 offsets_to_byte_indices[byte_index_count]
            u2 byte2_index_count
            u1 offsets_to_byte2_indices[byte2_index_count]
        }
    '''
    def __init__(self, tlv):
        Component.__init__(self, tlv)

#----------------------------------------------------------------------------
class Descriptor(Component):
    '''
        descriptor_component {
            u1 tag
            u2 size
            u1 class_count
            class_descriptor_info classes[class_count]
            type_descriptor_info types
        }
    '''
    def __init__(self, tlv):
        Component.__init__(self, tlv)

#----------------------------------------------------------------------------
class Class_debug_info(object):
    '''
        class_debug_info {
            u2 name_index
            u2 access_flags
            u2 location
            u2 superclass_name_index
            u2 source_file_index
            u1 interface_count
            u2 field_count
            u2 method_count
            u2 interface_names_indexes[interface_count]
            field_debug_info fields[field_count]
            method_debug_info methods[method_count]
        }
    '''
    def __init__(self, data):
        pass

    def __str__(self):
        return

class Debug(Component):
    '''
        debug_component {
            u1 tag
            u2 size
            u2 string_count
            utf8_info strings_table[string_count]
            u2 package_name_index
            u2 class_count
            class_debug_info classes[class_count]
        }
    '''
    def __init__(self, tlv):
        Component.__init__(self, tlv)

        # strings_table
        count = getshort(self.info[:2])
        v = self.info[2:]
        self.strings_table = []
        j = 0
        for i in range(count):
            lgth = getshort(v[j:j+2])
            utf8_info = v[j+2:j+2+lgth]
            j += 2+lgth
            self.strings_table.append(utf8_info)

        # package name
        v = v[j:]
        self.package_name = self.strings_table[getshort(v[:2])]
        j += 2

        # class
        v = v[2:]
        count = getshort(v[:2])
        v = v[2:]

        self.classes = []
        for i in range(count):
            pass


#----------------------------------------------------------------------------
class CapEditor(object):

    ''' <JavaCard222VMspec.pdf>, chapter 6, The CAP File Format '''

    def __init__(self, path):
        self.jar = zipfile.ZipFile(path, 'r') # a zipfile
        self.parse()

    def parse(self):
        ''' 
            net/sourceforge/globalplatform/jc/helloworld/javacard/Header.cap
            net/sourceforge/globalplatform/jc/helloworld/javacard/Directory.cap
            net/sourceforge/globalplatform/jc/helloworld/javacard/Applet.cap
            net/sourceforge/globalplatform/jc/helloworld/javacard/Import.cap
            net/sourceforge/globalplatform/jc/helloworld/javacard/ConstantPool.cap
            net/sourceforge/globalplatform/jc/helloworld/javacard/Class.cap
            net/sourceforge/globalplatform/jc/helloworld/javacard/Method.cap
            net/sourceforge/globalplatform/jc/helloworld/javacard/StaticField.cap
            net/sourceforge/globalplatform/jc/helloworld/javacard/RefLocation.cap
            net/sourceforge/globalplatform/jc/helloworld/javacard/Descriptor.cap
        '''
        filenames = map(lambda x:x.filename, self.jar.infolist())
        paths = filter(lambda x:x.endswith('.cap'), filenames) # we don't care other files
        pattern = re.compile(r'^([0-9a-zA-Z//]+/)javacard/(\w+\.cap)')
        self.components = dict([(pattern.match(path).group(1), self.jar.read(path)) for path in paths]) # a dictionary
 
    def __str__(self, descriptor=False, debug=False):
        ''' joins all cap files to form a binary string '''
        s = ''
        for x in SEQUENCE[:-2]:
            s += self.components.get(x, '')

        if descriptor:
            s += self.components.get(SEQUENCE[-2], '')
        if debug:
            s += self.components.get(SEQUENCE[-1], '')
        return s

    def __getitem__(self, key):
        return self.components.get(key, '')


#----------------------------------------------------------------------------
class TestModule(unittest.TestCase):
    ''' 本模块的单元测试 '''

    def test_helloworld(self):
        pass

#-------------------------------------------------------------------------------
if __name__ == '__main__':
    FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    unittest.main()

