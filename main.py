#!/usr/bin/env python
# -*- coding: utf8 -*-

import sys, os, logging
import wx

import xinghan_ico
import api_config
import ui_notebook


#----------------------------------------------------------------------
# define API
def u(utf8):
    return utf8.decode('utf8')

XH = u('星汉智能卡检测系统')

#----------------------------------------------------------------------------

class Log:
    def WriteText(self, text):
        if text[-1:] == '\n':
            text = text[:-1]
        wx.LogMessage(text)
    write = WriteText


#----------------------------------------------------------------------------

#class RunDemoApp(wx.App, wx.lib.mixins.inspection.InspectionMixin):
class RunDemoApp(wx.App):

    # http://www.wxpython.org/docs/api/wx.lib.infoframe-module.html
    #outputWindowClass = PyInformationalMessagesFrame

    def __init__(self, name, module, useShell, redirect=False, redirectpath=r'.\svs.log'):

        self.name = name
        self.demoModule = module
        self.useShell = useShell
        self.redirectpath = redirectpath
        wx.App.__init__(self, redirect=redirect)

    def OnInit(self):
        wx.Log.SetActiveTarget(wx.LogStderr())

        #self.SetAssertMode(assertMode)
        #self.InitInspection()  # for the InspectionMixin base class

        style = wx.DEFAULT_FRAME_STYLE
        frame = wx.Frame(None, -1, XH, pos=(-1,-1), size=(-1,-1), style=style)
        menuBar = wx.MenuBar()
        menu = wx.Menu()
        item = menu.Append(-1, u("保存日记到文件"), u("将日记保存到文件中"))
        self.Bind(wx.EVT_MENU, self.OnLogToFile, item)
        #item = menu.Append(-1, "&Widget Inspector\tF6", "Show the wxPython Widget Inspection Tool")
        #self.Bind(wx.EVT_MENU, self.OnWidgetInspector, item)
        item = menu.Append(wx.ID_EXIT, u("退出"), u("关闭并退出"))
        self.Bind(wx.EVT_MENU, self.OnExitApp, item)
        menuBar.Append(menu, u("文件"))

        menu = wx.Menu()
        item = menu.Append(-1, u("关于"), u("软件信息"))
        self.Bind(wx.EVT_MENU, self.OnAbout, item)
        menuBar.Append(menu, u("帮助"))

        ns = {}
        ns['wx'] = wx
        ns['app'] = self
        ns['module'] = self.demoModule
        ns['frame'] = frame

        frame.Center()
        frame.CenterOnScreen()
        frame.CreateStatusBar()
        frame.SetMenuBar(menuBar)
        frame.SetIcon(xinghan_ico.xinghan.GetIcon())
        frame.Show(True)
        frame.Bind(wx.EVT_CLOSE, self.OnCloseFrame)

        win = self.demoModule.runTest(frame, frame, Log())

        # a window will be returned if the demo does not create
        # its own top-level window
        if win:
            # so set the frame to a good size for showing stuff
            #frame.SetClientSize(win.GetBestSize())
            frame.Maximize()
            win.SetFocus()
            self.window = win
            ns['win'] = win
            frect = frame.GetRect()
        else:
            # It was probably a dialog or something that is already
            # gone, so we're done.
            frame.Destroy()
            return True

        self.SetTopWindow(frame)
        #wx.Log_SetActiveTarget(wx.LogStderr())
        #wx.Log_SetTraceMask(wx.TraceMessages)

        if self.useShell:
            # Make a PyShell window, and position it below our test window
            from wx import py
            shell = py.shell.ShellFrame(None, locals=ns)
            frect.OffsetXY(0, frect.height)
            frect.height = 400
            shell.SetRect(frect)
            shell.Show()

            # Hook the close event of the test window so that we close
            # the shell at the same time
            def CloseShell(evt):
                if shell:
                    shell.Close()
                evt.Skip()
            frame.Bind(wx.EVT_CLOSE, CloseShell)
                    
        # redirect output
        if redirect:
            app = wx.GetApp()
            app.RedirectStdio(redirectpath)

        self.frame = frame
        return True

    def OnAbout(self, evt):
        info = wx.AboutDialogInfo()
        info.Name = XH
        info.Version = "0.1.0"
        info.Copyright = "(C) 2016 Zhuhai XH Smartcard Co., Ltd"
        info.WebSite = "http://www.china-xinghan.com"
        #info.Developers = ["wg@china-xinghan.com", "xhrd@china-xinghan.com"]
        info.Developers = ["xhrd@china-xinghan.com",]
        wx.AboutBox(info)

    def OnExitApp(self, evt):
        self.frame.Close(True)
        wx.Log.SetActiveTarget(None)
        evt.Skip()

    def OnCloseFrame(self, evt):
        if hasattr(self, "window") and hasattr(self.window, "ShutdownDemo"):
            self.window.ShutdownDemo()
        self.ExitMainLoop()
        evt.Skip()

    #def OnWidgetInspector(self, evt):
        #wx.lib.inspection.InspectionTool().Show()

    def OnLogToFile(self, evt):
        app = wx.GetApp()
        app.RedirectStdio(redirectpath)
 

#----------------------------------------------------------------------------
if __name__ == "__main__":
    cfg = api_config.CONFIG
    useShell = cfg.getboolean(__name__, 'useshell')
    redirect = cfg.getboolean(__name__, 'redirect')
    redirectpath = cfg.get(__name__, 'redirectpath')

    #LOGGING_LEVEL = api_config.CONFIG.getint(__name__, 'logginglevel')
    #FMT = api_config.CONFIG.get(__name__, 'loggingformat')
    #logging.basicConfig(level=LOGGING_LEVEL, format=FMT)

    import api_alg
    import api_app
    import api_barcode
    import api_cap
    import api_config
    import api_crc
    import api_datacenter
    import api_filesystem
    import api_general
    import api_gp
    import api_incarddata
    import api_inputdata
    import api_pcsc
    import api_print
    import api_tlv
    import api_unittest
    import api_util
    import api_validators
    import api_virtualcap
    #import Crypto.Cipher.DES
    #import Crypto.Cipher.DES3
    import Crypto

    app = RunDemoApp('ui_notebook', ui_notebook, useShell, redirect, redirectpath)
    app.MainLoop()


