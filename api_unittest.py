#!/usr/env python
# -*- coding: utf-8 -*-

""" API related with Unit Test.

The module encapsluates Unit Test fuctions for tester's convinence.

__author__ = "XH Smart Card Co,.Ltd. http://www.china-xinghan.com/smartcard/en/"
__date__ = "Aug 2016"
__version__ = "0.1.0"

Copyright 2016 XH Smart Card Co,. Ltd

Author: wg@china-xinghan.com
"""

import os, sys, imp, unittest, logging, collections
import api_config
import HTMLTestRunner # 不在python的site-packages中。直接在XHSVS目录里。

#----------------------------------------------------------------------------
Logger = logging.getLogger(__name__)


#----------------------------------------------------------------------------
class TestCase(unittest.TestCase):

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        self.logger = logging.getLogger(self.__class__.__name__) # to simplify logging operations while testing

class TestLoader(unittest.TestLoader):
    pass

class TestSuite(unittest.TestSuite):

    def run(self, result, debug=False, thread_instance=None):
        ''' Override to provide 'Progress' feature
        '''
        topLevel = False
        if getattr(result, '_testRunEntered', False) is False:
            result._testRunEntered = topLevel = True

        for test in self:
            if result.shouldStop:
                break

            if unittest.suite._isnotsuite(test):
                self._tearDownPreviousClass(test, result)
                self._handleModuleFixture(test, result)
                self._handleClassSetUp(test, result)
                result._previousTestClass = test.__class__

                if (getattr(test.__class__, '_classSetupFailed', False) or
                    getattr(result, '_moduleSetUpFailed', False)):
                    continue

            if not debug:
                test(result)
                if thread_instance:
                    if unittest.suite._isnotsuite(test):
                        thread_instance.PostTestResult(result)
            else:
                test.debug()
                if thread_instance:
                    if unittest.suite._isnotsuite(test):
                        thread_instance.PostTestResult(result)

        if topLevel:
            self._tearDownPreviousClass(None, result)
            self._handleModuleTearDown(result)
            result._testRunEntered = False
        return result

HTML_PATH = api_config.CONFIG.get(__name__, 'htmlpath')
LOGGING_LEVEL = api_config.CONFIG.getint(__name__, 'logginglevel')
FMT = api_config.CONFIG.get(__name__, 'loggingformat')
VERBOSITY = api_config.CONFIG.getint(__name__, 'verbosity')

#----------------------------------------------------------------------------
def htmlunittest(testsuite, html_title, html_description, html_path=None, logging_level=None, verbosity=None, thread_instance=None):
    ''' '''
    title = html_title
    if type(html_title) != type(u''):
        title = html_title.decode('utf-8')
    description = html_description
    if type(html_description) != type(u''):
        description = html_description.decode('utf-8')

    html_path = html_path if html_path else os.path.join(HTML_PATH, html_title+'.html')
    logging_level = logging_level if logging_level else LOGGING_LEVEL
    verbosity = verbosity if verbosity else VERBOSITY

    runner = HTMLTestRunner.HTMLTestRunner(
                stream=open(html_path, 'wb'),
                verbosity=verbosity,
                title=title,
                description=description,
                thread_instance=thread_instance,
                )

    # Use an external stylesheet.
    # See the Template_mixin class for more customizable options
    #runner.STYLESHEET_TMPL = '<link rel="stylesheet" href="my_stylesheet.css" type="text/css">'

    # config Logging
    logging.basicConfig(level=logging_level, format=FMT, stream=HTMLTestRunner.stdout_redirector)

    # run the test
    return runner.run(testsuite), os.path.abspath(html_path)


#----------------------------------------------------------------------------
def importmodule(code,name,add_to_sys_modules=0):
    """
    http://code.activestate.com/recipes/82234-importing-a-dynamically-generated-module/
    https://docs.python.org/2.7/reference/simple_stmts.html#exec

    Import dynamically generated code as a module. code is the
    object containing the code (a string, a file handle or an
    actual compiled code object, same types as accepted by an
    exec statement). The name is the name to give to the module,
    and the final argument says wheter to add it to sys.modules
    or not. If it is added, a subsequent import statement using
    name will return this module. If it is not added to sys.modules
    import will try to load it in the normal fashion.

    import foo

    is equivalent to

    foofile = open("/path/to/foo.py")
    foo = importmodule(foofile,"foo",1)

    Returns a newly generated module.
    """
    module = imp.new_module(name)
    code = '\n'.join(code.splitlines()) # Note that the parser only accepts the Unix-style end of line convention.
    #exec code in module.__dict__
    eval(code, globals())
    if add_to_sys_modules:
        sys.modules[name] = module

    return module

def importmodule1(name, fp, fppath, description=('.py', 'U', 1)):
    try:
        return imp.load_module(name, fp, fppath, description)
    except ImportError as e:
        raise
    finally:
        if fp:
            fp.close()

def getcappath(name):
    cfg = api_config.CONFIG
    root = cfg.get(__name__, 'root')
    return os.path.join(root, name)

def gettestsuite():
    cfg = api_config.CONFIG
    root = cfg.get(__name__, 'root')
    #fp = open('svs_log.txt', 'wb')
    add_to_sys_modules = cfg.getboolean(__name__, 'add_to_sys_modules')
    prefix = cfg.get(__name__, 'prefix')
    suffix = cfg.get(__name__, 'suffix')

    lst = filter(lambda x:x.startswith(prefix) and x.endswith(suffix), os.listdir(root))
    lst = map(lambda x:os.path.abspath(os.path.join(root, x)), lst)
    lst = filter(os.path.isfile, lst)

    dit = collections.OrderedDict()
    for x in lst:
        tail = os.path.split(x)[1]
        name = tail[:-len(suffix)]
        try:
            #module = importmodule(open(x, 'rb').read(), name, add_to_sys_modules)
            module = importmodule1(name, open(x, 'rb'), x)
        except Exception as e:
            Logger.error("Invalid test script file: %s , please correct its synatx error:\n%s" % (x, str(e)))
            continue

        suite = TestLoader().loadTestsFromModule(module)
        if suite:
            total = sum(map(lambda x:x.countTestCases(), suite))
            if total:
                dit[name] = (name, x, module, suite) # file name, abspath, python module, python testsuite
            else:
                Logger.error("No test_XXXX found in %s, please make sure your have written any test methods in it" % x)
        else:
            Logger.error("No Testcase sub-class found in %s, please make sure you have the right test script" % x)

    return dit

def gettestcaseclazzname(suite):
    if len(suite._tests) > 0:
        name = suite._tests[0].__class__.__name__
    else:
        name = suite.__class__.__name__
    return name

#----------------------------------------------------------------------------
class TestModule(unittest.TestCase):
    ''' 本模块的单元测试 '''

    def test_logger(self):
        class TestCase1(TestCase):
            def runTest(self): pass
        tc1 = TestCase1('runTest', a=1, b=2, c=3, d='4', e=(5,6,7), f={8:8, '9':9, '10':'10', '11':(11,12)})
        self.assertTrue(hasattr(tc1, 'logger'))
        self.assertTrue(None==tc1.logger.debug('debug'))
        self.assertTrue(None==tc1.logger.info('info'))
        self.assertTrue(None==tc1.logger.warning('warning'))
        self.assertTrue(None==tc1.logger.error('error'))


def test_htmltestrunner():
    import webbrowser
    import os
    class TestCase1(TestCase):
        ''' 测试案例1 '''
        def test_1(self):
            ''' 测试1 '''
            pass

    loader = TestLoader()
    suite = loader.loadTestsFromTestCase(TestCase1)
    path = os.path.abspath(r'.\api_unittest.html')
    # def htmlunittest(testsuite, html_title, html_description, html_path, logging_level):
    result = htmlunittest(suite, TestCase1.__name__, TestCase1.__doc__, path, logging.DEBUG, 2)
    webbrowser.open('file://'+path)

#----------------------------------------------------------------------------
if __name__=='__main__':
    unittest.main()
    #test_htmltestrunner()

