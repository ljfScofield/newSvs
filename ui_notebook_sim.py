#!/usr/env python
# -*- coding: utf-8 -*-

import os, time, urllib, thread, traceback

import wx
import wx.lib.dialogs
import wx.lib.agw.customtreectrl as CT
import wx.html2 as webview
import wx.aui
import string

import api_pcsc
import api_util
import api_config
import ui_notebook_cos
import api_unittest
import ui_client
import api_print
import MySQLdb
#----------------------------------------------------------------------
# define API
u = api_util.u
VisualCard = api_print.VisualCard
MsgDlg = wx.lib.dialogs.ScrolledMessageDialog
Printer = None

TITLE = u('SIM')

#----------------------------------------------------------------------
# This creates a new Event class and a EVT binder function
(TestResultEvent, EVT_TEST_RESULT) = wx.lib.newevent.NewEvent()
(LoadHtmlEvent, EVT_LOAD_HTML) = wx.lib.newevent.NewEvent()
(TestFinishedEvent, EVT_TEST_FINISHED) = wx.lib.newevent.NewEvent()
(TestException, EVT_TEST_EXCEPTION) = wx.lib.newevent.NewEvent()
(SimUiEvent, EVT_SIM_UI) = wx.lib.newevent.NewEvent() #事件类型，绑定对象


#----------------------------------------------------------------------
class TestThread:
    def __init__(self, win, testsuites):
        self.win = win
        self.testsuites = testsuites

    def Start(self):
        self.keepGoing = True
        self.running = True
        thread.start_new_thread(self.Run, ())

    def Stop(self):
        self.keepGoing = False

    def IsRunning(self):
        return self.running

    def Run(self):
        try:
            for suite, name, doc in self.testsuites:
                if self.keepGoing:
                    doc = doc if doc else ''
                    result, htmlpath = api_unittest.htmlunittest(suite, name, doc, thread_instance=self)
                    self.PostHtml(result, htmlpath, name)
        except Exception as e:
            self.PostTestException(e, traceback.format_exc(e))
            return
        finally:
            self.running = False

        self.PostTestFinished()

    def PostTestFinished(self):
        # We communicate with the UI by sending events to it. There can be
        # no manipulation of UI objects from the worker thread.
        evt = TestFinishedEvent()
        wx.PostEvent(self.win, evt)

    def PostHtml(self, result, htmlpath, title):
        # We communicate with the UI by sending events to it. There can be
        # no manipulation of UI objects from the worker thread.
        evt = LoadHtmlEvent(result=result, htmlpath=htmlpath, title=title)
        wx.PostEvent(self.win, evt)

    def PostTestResult(self, result):
        # We communicate with the UI by sending events to it. There can be
        # no manipulation of UI objects from the worker thread.
        evt = TestResultEvent()
        evt.result = result
        wx.PostEvent(self.win, evt)

    def PostTestException(self, exception, msg=None):
        # We communicate with the UI by sending events to it. There can be
        # no manipulation of UI objects from the worker thread.
        evt = TestException()
        evt.exception = exception
        evt.msg = msg
        wx.PostEvent(self.win, evt)
        
    def PostSimUiEvent(self, texts, barcodes):
        evt= SimUiEvent()
        evt.texts = texts
        evt.barcodes = barcodes
        wx.PostEvent(self.win, evt)

#----------------------------------------------------------------------
class BasicPanel(wx.Panel):
    ''' 基础UI，封装了一些方便的弹出消息框、日记方法等API '''

    def __init__(self, parent, size=(-1,-1)):
        wx.Panel.__init__(self, parent, -1, size=size)

    def showerror(self, title, msg, style=wx.ICON_ERROR|wx.ICON_HAND):
        dlg = wx.MessageDialog(self, u(msg), u(title), style=style)
        dlg.ShowModal()
        dlg.Destroy()

    def showmsg(self, title, msg):
        dlg = wx.MessageDialog(self, u(msg), u(title))
        dlg.ShowModal()
        dlg.Destroy()

    def showlongmsg(self, title, msg):
        dlg = MsgDlg(self, u(msg), u(title))
        dlg.ShowModal()
        dlg.Destroy()



#----------------------------------------------------------------------
def Mysqldata(order, iccid, pin1 , puk1, hlr, PRINT_REGION):
    ''' 测试Mysqldata数据:        
        order: 订单号
        PRINT_ICCID: 
        PRINT_HLR:
        pin1PRINT_PIN1:
        PRINT_PUK1：
        PRINT_REGION
        printer: 测试软件提供的虚拟打印机，用于打印文本、条形码到虚拟卡面
    '''
    # 2. 打印版面：文本、条形码
    w, h = Printer.getwidthheight()
    x, y = Printer.getsmallcardposition()
    w1, h1 = Printer.getsmallcardwidthheight()
    telcel_texts = [
            ('PIN1: '+pin1 + '    PUK1: '+puk1, (w*0.5, h*0.1)),
            (iccid[:10], (x+w1*0.3, y+h1*0.1)),
            (hlr,        (x+w1*0.6, y+h1*0.3)),
            (iccid[10:], (x+w1*0.3, y+h1*0.6)),
            (iccid[:-1] +'  '+ hlr+' '+ PRINT_REGION, (w*0.1, h*0.9)),
            ]
    barcodes = [
            # 内容、位置、编码格式
            (iccid[:-1], (w*0.1, h*0.6), 'CODE128'),
            ]
    visual = VisualCard(Printer)
    visual.settexts(telcel_texts).setbarcodes(barcodes)

#------------------------------------------------------------------------
def cleanPrinter():
    ''' clean 测试软件提供的虚拟打印机，用于打印文本、条形码到虚拟卡面
    '''
    # 2. 打印版面：文本、条形码
    w, h = Printer.getwidthheight()
    x, y = Printer.getsmallcardposition()
    w1, h1 = Printer.getsmallcardwidthheight()
    telcel_texts = [('',(w*0.5, h*0.1)),
                    ('', (x+w1*0.3, y+h1*0.1)),
                    ('',        (x+w1*0.6, y+h1*0.3)),
                    ('', (x+w1*0.3, y+h1*0.6)),
                    ('', (w*0.1, h*0.9)),
                   ]
    barcodes = [('',(w*0.1, h*0.6),'CODE128'),] 
    visual = VisualCard(Printer)
    visual.settexts(telcel_texts).setbarcodes(barcodes) 


#----------------------------------------------------------------------
ArtIDs = [
    wx.ART_FOLDER,
    wx.ART_FOLDER_OPEN,
    wx.ART_EXECUTABLE_FILE,
    wx.ART_NORMAL_FILE,
           ]

'''
         =============== =========================================
         `ct_type` Value Description
         =============== =========================================
                0        A normal item
                1        A checkbox-like item
                2        A radiobutton-type item
         =============== =========================================
'''
ct_type_normal = 0
ct_type_checkbox = 1
ct_type_radio = 2

class TestsuiteTreeCtrl(CT.CustomTreeCtrl):

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.SUNKEN_BORDER|wx.WANTS_CHARS,
                 agwStyle=CT.TR_HAS_BUTTONS|CT.TR_AUTO_CHECK_CHILD|CT.TR_AUTO_CHECK_PARENT,
                 rootlabel='sim_Testsuites',
                 testsuites={},
                 ):
        CT.CustomTreeCtrl.__init__(self, parent, id, pos, size, style, agwStyle)
        self.SetBackgroundColour(wx.WHITE)
        self.rootlabel = rootlabel

        il = wx.ImageList(16, 16)
        for items in ArtIDs[1:-1]:
            bmp = wx.ArtProvider_GetBitmap(items, wx.ART_TOOLBAR, (16, 16))
            il.Add(bmp)
        self.AssignImageList(il)

        label = rootlabel if testsuites else 'No Testsuite found'
        self.root = self.AddRoot(label, ct_type=ct_type_checkbox)
        self.SetItemImage(self.root, 0, CT.TreeItemIcon_Normal)
        self.SetItemImage(self.root, 1, CT.TreeItemIcon_Expanded)
        self.SetPyData(self.root, testsuites)

        for py, v in testsuites.items():
            level1 = self.AppendItem(self.root, py, ct_type=ct_type_checkbox)
            self.SetPyData(level1, v) # v: file name, abspath, python module, python testsuite
            self.SetItemImage(level1, 0, CT.TreeItemIcon_Normal)
            self.SetItemImage(level1, 1, CT.TreeItemIcon_Expanded)
            #level1.Check()

            name, abspath, module, suite = v
            for clazz in suite:
                level2 = self.AppendItem(level1, api_unittest.gettestcaseclazzname(clazz), ct_type=ct_type_checkbox)
                self.SetPyData(level2, clazz)
                self.SetItemImage(level2, 0, CT.TreeItemIcon_Normal)
                self.SetItemImage(level2, 1, CT.TreeItemIcon_Expanded)
                #level2.Check()

                for test_ in clazz:
                    level3 = self.AppendItem(level2, test_._testMethodName)
                    self.SetPyData(level3, test_)
                #self.Expand(level2)
            self.Expand(level1)

        self.Expand(self.root)
        #self.root.Check()

        self.Bind(wx.EVT_CONTEXT_MENU, self.OnContextMenu)

    def OnContextMenu(self, event):
        # Popup menu: reload
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.Bind(wx.EVT_MENU, self.OnPopup1, id=self.popupID1)

        menu = wx.Menu() # make a menu
        item = wx.MenuItem(menu, self.popupID1, "Reload") # Show how to put an icon in the menu
        menu.AppendItem(item)

        self.PopupMenu(menu)
        menu.Destroy()

    def reload(self, testsuites):
        self.DeleteAllItems()

        label = self.rootlabel if testsuites else 'No Testsuite found'
        self.root = self.AddRoot(label, ct_type=ct_type_checkbox)
        self.SetItemImage(self.root, 0, CT.TreeItemIcon_Normal)
        self.SetItemImage(self.root, 1, CT.TreeItemIcon_Expanded)
        self.SetPyData(self.root, testsuites)

        for py, v in testsuites.items():
            level1 = self.AppendItem(self.root, py, ct_type=ct_type_checkbox)
            self.SetPyData(level1, v) # v: file name, abspath, python module, python testsuite
            self.SetItemImage(level1, 0, CT.TreeItemIcon_Normal)
            self.SetItemImage(level1, 1, CT.TreeItemIcon_Expanded)
            #level1.Check()

            name, abspath, module, suite = v
            for clazz in suite:
                level2 = self.AppendItem(level1, api_unittest.gettestcaseclazzname(clazz), ct_type=ct_type_checkbox)
                self.SetPyData(level2, clazz)
                self.SetItemImage(level2, 0, CT.TreeItemIcon_Normal)
                self.SetItemImage(level2, 1, CT.TreeItemIcon_Expanded)
                #level2.Check()

                for test_ in clazz:
                    level3 = self.AppendItem(level2, test_._testMethodName)
                    self.SetPyData(level3, test_)
                #self.Expand(level2)
            self.Expand(level1)

        self.Expand(self.root)
        #self.root.Check()

    def OnPopup1(self, event):
        p = self.GetParent()
        if p:
            p.OnReload()


class ClientPanel(BasicPanel):
    ''' 绘制主界面UI '''

    def __init__(self, parent):
        # init
        BasicPanel.__init__(self, parent)

        # box1: readers, reset, start, stop
        self.readers = api_pcsc.getreaderlist()
        self.reader_combo = wx.ComboBox(self, -1, '', (-1,-1), (-1,-1), map(str, self.readers), style=wx.CB_READONLY)
        self.reset_but = wx.Button(self, -1, 'Reset', (-1, -1))
        if self.readers:
            self.reader_combo.SetSelection(0)
        #self.reader_combo.Hide()
        #self.reset_but.Hide()
        self.Bind(wx.EVT_COMBOBOX, self.OnSelectReader, self.reader_combo)
        self.Bind(wx.EVT_BUTTON, self.OnReset, self.reset_but)

        self.gauge = wx.Gauge(self, -1, 300)#
        self.start_but = wx.Button(self, -1, '开始', (-1, -1))
        self.stop_but = wx.Button(self, -1, '停止', (-1, -1))

        self.txt_but = wx.TextCtrl(self, -1, "", size=(650, -1),style=wx.TE_RICH2) #iccid文本
        self.txt_but.SetStyle(0, 32, wx.TextAttr("", "white"))      
        self.txt_iccid = wx.StaticText(self, -1, "ICCID:")
        self.txt_but1 = wx.TextCtrl(self, -1, "", size=(650, -1),style=wx.TE_RICH2)#单号文本
        self.txt_but1.SetStyle(0, 32, wx.TextAttr("", "white"))
        self.txt_data = wx.StaticText(self, -1, "工单号:")
        
        sb = wx.StaticBox(self, -1, "期待版面：")  #版面box
        sbsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
        global Printer
        Printer = ui_client.PrinterPanel(sb)
        sbsizer.Add(Printer, 0) 

                
        self.gauge.SetValue(0)
        self.Bind(wx.EVT_BUTTON, self.OnStart, self.start_but)
        self.Bind(wx.EVT_BUTTON, self.OnStop, self.stop_but)

    
        box1 = wx.BoxSizer(wx.HORIZONTAL)          
        box1.Add(self.reader_combo, 1, wx.EXPAND)
        box1.Add(self.reset_but, 0, wx.EXPAND)
        box1.Add(self.gauge, 1, wx.EXPAND)
        box1.Add(self.start_but, 0, wx.EXPAND)
        box1.Add(self.stop_but, 0, wx.EXPAND)
      
        
        box3 = wx.BoxSizer(wx.HORIZONTAL)
        box3.Add(self.txt_iccid, 1, wx.EXPAND)
        box3.Add(self.txt_but, 1, wx.EXPAND)        
        box3.Add(self.txt_data, 1, wx.EXPAND) 
        box3.Add(self.txt_but1, 1, wx.EXPAND)
        

       # box2: testsuites, htmls
        self.testsuites = self.GetTestsuites()
        self.testsuites_tree = TestsuiteTreeCtrl(self, -1, testsuites=self.testsuites)
        self.html_nb = wx.aui.AuiNotebook(self, style=wx.aui.AUI_NB_DEFAULT_STYLE)
        
        box4 = wx.BoxSizer(wx.VERTICAL)         
        box4.Add(self.testsuites_tree, 1, wx.EXPAND)
        box4.Add(sbsizer, 1, wx.EXPAND)
        

        box2 = wx.BoxSizer(wx.HORIZONTAL)
        box2.Add(box4, 3, wx.EXPAND)
        box2.Add(self.html_nb, 5, wx.EXPAND)
        


        # finally
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(box1, 0, wx.EXPAND)
        box.Add(box3, 0, wx.BOTTOM)
        box.Add(box2, 1, wx.EXPAND)
        

        self.start_but.Enable()
        self.stop_but.Disable()
        self.gauge.SetValue(0)

        self.SetSizer(box)
        #self.GetBestSize()

        # thread
        self.thread, self.t0 = None, 0
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.Bind(EVT_TEST_RESULT, self.OnTestResult)
        self.Bind(EVT_LOAD_HTML, self.OnLoadHtml)
        self.Bind(EVT_TEST_FINISHED, self.OnTestFinished)
        self.Bind(EVT_TEST_EXCEPTION, self.OnTestException)
        self.Bind(EVT_SIM_UI, self.OnSIMUI)

    def OnReload(self):
        self.testsuites_tree.reload(self.GetTestsuites())

    def GetTestsuites(self):
        try:
            return api_unittest.gettestsuite_sim()
        except Exception as e:
            self.showerror('测试脚本语法不正确，请检查后重新打开测试工具', str(e))
            return dict()

    def OnTestFinished(self, evt):
        self.OnStop()

        t1 = time.clock()
        time.sleep(0.1)
        if self.thread:
            if not self.thread.IsRunning(): # all finished
                self.start_but.Enable()
                self.stop_but.Disable()
                
                t = t1-self.t0
                executed, total = self.gauge.GetValue(), self.gauge.GetRange()
                if executed==total:
                    self.showmsg('测试全部完成', '%d 个测试案例\n用时 %.3f 秒' % (total, t))
                else:
                    self.showerror('测试部分完成', '已执行 %d/%d 个测试案例\n用时 %.3f 秒' % (executed, total, t))

    def OnTestException(self, evt):
        self.OnStop()
        self.showerror('测试出现异常，已终止', evt.msg)

    def OnTestResult(self, evt):
        v = self.gauge.GetValue()
        self.gauge.SetValue(v+1)

    def OnLoadHtml(self, evt):
        result, htmlpath, title = evt.result, evt.htmlpath, evt.title
        self.loadhtml(htmlpath, title)
        
    def OnSIMUI(self, evt):
        texts, barcodes = evt.texts, evt.barcodes
        Printer.settexts(texts)
        Printer.setbarcodes(barcodes)
        #

    def stopthread(self):
        if self.thread:
            if self.thread.IsRunning():
                busy = wx.BusyInfo(u('稍等，正在关闭后台线程'))
                wx.Yield()

                while self.thread.IsRunning():
                    self.thread.Stop()
                    time.sleep(0.1)

    def OnCloseWindow(self, evt):
        self.stopthread()
        self.Destroy()
            

    def OnStart(self, event):         
        if not api_config.test_exe_path():
            self.showerror('配置错误', '%s\n请不要将svs.exe放在中文等特殊路径，建议放在纯英文路径' % os.path.abspath(os.getcwd()))
            return

        order = self.txt_but1.GetValue()
        iccid = self.txt_but.GetValue()
        if order == '' or iccid == '' or not(all([c in string.hexdigits for c in iccid])) :
            self.showerror("错误",'请输入正确的ICCID和订单号')  
            return
 
        try:
            self.SetMysqlDatas(iccid, order)
        except Exception as e:            
            self.showerror("Set Mysql data error", str(e))
            #cleanPrinter()
            return
            
        self.start_but.Disable()
        self.stop_but.Enable()

        lst = []
        root = self.testsuites_tree.root
        for py in root.GetChildren():
            clazzs = filter(lambda clazz:clazz.IsChecked(), py.GetChildren())
            if len(clazzs):
                suite = api_unittest.TestSuite()
                for clazz in clazzs:
                    suite.addTests(self.testsuites_tree.GetPyData(clazz))
                module = self.testsuites_tree.GetPyData(py)[2] # v: file name, abspath, python module, python testsuite
                lst.append((suite, module.__name__, module.__doc__))

        if not lst:
            self.OnStop()

        total = sum(map(lambda x:x[0].countTestCases(), lst))
        self.gauge.SetValue(0)
        self.gauge.SetRange(total)
        time.sleep(0.01)

        self.t0 = time.clock()
        self.thread = TestThread(self, lst)
        self.thread.Start()    
        
       
    def SetMysqlDatas(self, iccid, order):  
        ip, name, pwd, db = api_config.get_mysql_params()
        ksql = "SELECT * FROM sim" 
        dsql = "SELECT * FROM sim WHERE ICCID = '%s'" % (iccid)

        try:
            db = MySQLdb.connect(ip, name, pwd, db)
            cursor = db.cursor()
            cursor.execute(ksql)
            keys = [tuple[0] for tuple in cursor.description] # a tuple, ('ICCID', )
            
            cursor.execute(dsql)
            datas = cursor.fetchall()[0] # a list, ['89', ]             
            
        except:
            print "research mysql data exception"           
            raise
        finally:             
            db.close()
        
        api_config.set_mysql_keys(keys)
        api_config.set_mysql_datas(datas)
        return True

    def OnStop(self, event=None):
        self.start_but.Enable()
        self.stop_but.Disable()
        self.stopthread()

    def OnReset(self, event):
        try:
            api_pcsc.reset()
            atr = api_pcsc.getatr()
            self.showmsg('复位成功', 'ATR: ' + atr)
        except Exception as e:
            self.showlongmsg('复位失败', str(e))

    def OnSelectReader(self, event):
        name = str(self.readers[event.GetSelection()])
        try:
            api_pcsc.connectreader(name)
            self.showmsg("读卡器连接成功", name)
        except Exception as e:
            self.showlongmsg('读卡器连接失败', str(e))
            return
        api_config.set_default_pcsc_reader_name(name)

    def loadhtml(self, path, title):
        nb = self.html_nb
        url = 'file:' + urllib.pathname2url(path)

        for i in range(nb.GetPageCount()):
            page = nb.GetPage(i)
            if page.url == url:
                page.wv.Reload()
                break
        else:
            wv = webview.WebView.New(nb)
            nb.AddPage(wv, title, select=True)
            wv.LoadURL(url)
            self.Bind(webview.EVT_WEBVIEW_ERROR, self.OnWebViewError, wv)
            page = nb.GetCurrentPage()
            page.url = url
            page.wv = wv

    # WebView events
    def OnWebViewError(self, evt):
        with open('EVT_WEBVIEW_ERROR.txt', 'wb') as fp:
            fp.write(evt.GetString())
            
  

