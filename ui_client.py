#!/usr/env python
# -*- coding: utf-8 -*-

import string, binascii, os, logging, smartcard, traceback

import wx
import wx.lib.dialogs
import wx.lib.filebrowsebutton as filebrowse
import wx.lib.newevent
import wx.richtext
import wx.lib.agw.pybusyinfo as PBI

import api_app
import api_datacenter
import api_filesystem
import api_incarddata
import api_inputdata
import api_pcsc
import api_print
import api_util
import api_validators
import api_barcode

#----------------------------------------------------------------------
# define API
u = api_util.u
utf8toascii = api_util.utf8toascii
swap = api_util.swap

OrdernoValidator = api_validators.OrdernoValidator
ICCIDValidator = api_validators.ICCIDValidator

def checkIccidInput(text):
    '''
    '''
    if len(text) == 19:
        hexiccid = swap(text+'F')
    else:
        return False

#----------------------------------------------------------------------
MsgDlg = wx.lib.dialogs.ScrolledMessageDialog

# create event type
wxLogEvent, EVT_WX_LOG_EVENT = wx.lib.newevent.NewEvent()

GREEN = wx.Colour(0x00, 0xFF, 0x00)

class HexdigitsValidator(wx.PyValidator):
    def __init__(self):
        wx.PyValidator.__init__(self)
        self.Bind(wx.EVT_CHAR, self.OnChar)

    def Clone(self):
        return HexdigitsValidator()

    def Validate(self, win):
        val = self.GetWindow().GetValue()
        for x in val:
            if x not in string.hexdigits:
                return False

        return True

    def OnChar(self, event):
        key = event.GetKeyCode()

        if key < wx.WXK_SPACE or key == wx.WXK_DELETE or key > 255:
            event.Skip()
            return

        if chr(key) in string.hexdigits:
            event.Skip()
            return

        if not wx.Validator_IsSilent():
            wx.Bell()

        # Returning without calling even.Skip eats the event before it
        # gets to the text control
        return

#----------------------------------------------------------------------
class wxLogHandler(logging.Handler):
    """
    A handler class which sends log strings to a wx object
    """
    def __init__(self, wxDest):
        """
        Initialize the handler
        @param wxDest: the destination object to post the event to 
        @type wxDest: wx.Window
        """
        logging.Handler.__init__(self)
        self.wxDest = wxDest
        self.level = logging.DEBUG

    def flush(self):
        """
        does nothing for this handler
        """
        pass

    def emit(self, record):
        """
        Emit a record.
        """
        try:
            msg = self.format(record)
            evt = wxLogEvent(message=msg, levelno=record.levelno)
            wx.PostEvent(self.wxDest, evt)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


#----------------------------------------------------------------------
class BasicPanel(wx.Panel):
    ''' 基础UI，封装了一些方便的弹出消息框、日记方法等API '''

    def __init__(self, parent, size=(-1,-1)):
        wx.Panel.__init__(self, parent, -1, size=size)
        # logging setting
        self.logger = logging.getLogger(self.__class__.__name__)

    def info(self, msg, *args, **kwargs):
        self.logger.info(u(msg), *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(u(msg), *args, **kwargs)

    def showmsg(self, title, msg, style=wx.ICON_ERROR|wx.ICON_HAND):
        dlg = wx.MessageDialog(self, u(msg), u(title), style=style)
        dlg.ShowModal()
        dlg.Destroy()
        return

    def showlongmsg(self, title, msg):
        dlg = MsgDlg(self, u(msg), u(title))
        dlg.ShowModal()
        dlg.Destroy()
        return


#----------------------------------------------------------------------
class PrinterPanel(BasicPanel):
    ''' 可视卡UI，可以在其中绘制文本和条形码的 '''

    def __init__(self, parent):
        BasicPanel.__init__(self, parent, size=(170*3,106*3))

        self.texts, self.barcodes = None, None
        self.InitBuffer()
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, evt):
        # This automatically Blits self.buffer to a wx.PaintDC when
        # the dc is destroyed, and so nothing else needs done.
        dc = wx.BufferedPaintDC(self, self.buffer)#1 使用缓冲的内容刷新窗口

    def OnSize(self, evt):
        # When the window size changes we need a new buffer.
        self.InitBuffer()

    def InitBuffer(self):
        w, h = self.GetClientSize()
        self.buffer = wx.EmptyBitmap(w, h)
        dc = wx.BufferedDC(wx.ClientDC(self), self.buffer)
        self.Draw(dc)

    def Draw(self, dc):
        #dc.SetPen(wx.Pen("BLACK", 1))
        #dc.SetBrush(wx.Brush(GREEN))
        dc.Clear()
        w, h = self.GetClientSize()
        dc.DrawRoundedRectangle(0,0,w,h,radius=20)
        x, y = self.getsmallcardposition()
        w1,h1 = self.getsmallcardwidthheight()
        dc.DrawRoundedRectangle(x,y,w1,h1,radius=20)

        # draw texts
        if self.texts:
            texts = [t for t, p in self.texts]
            points = [p for t, p in self.texts]
            foregrounds = (wx.BLACK, ) * len(texts)
            dc.DrawTextList(texts, points, foregrounds, backgrounds=None)

        # draw Barcodes as Bitmap
        if self.barcodes:
            for t, p, codec in self.barcodes:
                wxbitmap = api_barcode.generate(codec, t, bar_width=3)
                # print 'wxbitmap height %d width %d' % (wxbitmap.GetHeight(), wxbitmap.GetWidth())
                # 176, 528
                dc.DrawBitmap(wxbitmap, p[0], p[1])

    def settexts(self, texts):
        ''' 将一系列文本texts，绘制到指定坐标开始的地方 '''
        if texts:
            self.texts = [(t, self.round(p)) for t, p in texts]
            dc = wx.BufferedDC(wx.ClientDC(self), self.buffer) # 因为数据改变了, 因此更新缓冲和窗口
            self.Draw(dc)

    def setbarcodes(self, barcodes):
        ''' 将一系列文本barcodes，以条形码的形式绘制到指定坐标开始的地方 '''
        if barcodes:
            self.barcodes = [(t, self.round(p), codec) for t, p, codec in barcodes]
            dc = wx.BufferedDC(wx.ClientDC(self), self.buffer) # 因为数据改变了, 因此更新缓冲和窗口
            self.Draw(dc)

    def getwidthheight(self):
        return self.GetClientSize()

    def getsmallcardwidthheight(self):
        w, h = self.GetClientSize()
        return w*0.3, h*0.3

    def getsmallcardposition(self):
        w, h = self.GetClientSize()
        return w*0.65, h*0.3

    def round(self, position):
        ''' 检查position是否超出范围 '''
        w, h = position
        width, height = self.GetClientSize()
        w1 = w if w<width else width
        h1 = h if h<height else height
        return w1,h1

#----------------------------------------------------------------------
class ClientPanel(BasicPanel):
    ''' 绘制主界面UI '''

    SN_Label = u('卡号')
    SN_Value = ''

    def __init__(self, parent):
        # init
        BasicPanel.__init__(self, parent)

        # box: input
        boxinput = wx.BoxSizer(wx.VERTICAL)

        # reader
        self.readers = api_pcsc.getreaderlist()
        self.readercombo = wx.ComboBox(self, -1, '', (-1,-1), (-1,-1), map(str, self.readers), style=wx.CB_READONLY)
        self.readercombo.SetSelection(0)

        b = wx.Button(self, -1, u('复位'), (-1, -1))
        self.Bind(wx.EVT_BUTTON, self.OnReset, b)

        boxreader = wx.BoxSizer(wx.HORIZONTAL)
        boxreader.Add(self.readercombo, 1, wx.EXPAND)
        boxreader.Add(b, 0, wx.EXPAND)

        # order
        boxinput.Add(boxreader, 0, wx.EXPAND)

        sb = wx.StaticBox(self, -1, u('XH工单号'))
        sbsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
        self.order = wx.TextCtrl(sb, -1, 'XH20160102', size=(-1,-1))
        sbsizer.Add(self.order, 1, wx.EXPAND|wx.ALL)
        boxinput.Add(sbsizer, 0, wx.EXPAND)

        # prd
        sb = wx.StaticBox(self, -1, u('prd数据文件'))
        sbsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
        self.prd = filebrowse.FileBrowseButtonWithHistory(self, -1, size=(170, -1), labelText='', buttonText=u('选择'), fileMask='*.prd', changeCallback=self.prdCallback)
        sbsizer.Add(self.prd, 1, wx.EXPAND|wx.ALL)
        boxinput.Add(sbsizer, 0, wx.EXPAND)

        boxiccidtest = wx.BoxSizer(wx.HORIZONTAL)
        # iccid
        sb = wx.StaticBox(self, -1, self.SN_Label)
        sbsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
        self.iccid = wx.TextCtrl(sb, -1, self.SN_Value, size=(-1,-1), validator=HexdigitsValidator())
        sbsizer.Add(self.iccid, 1, wx.EXPAND|wx.ALL)
        boxiccidtest.Add(sbsizer, 1, wx.EXPAND)

        # test
        b = wx.Button(self, -1, u('检测'), (-1, -1))
        self.Bind(wx.EVT_BUTTON, self.OnTest, b)
        boxiccidtest.Add(b, 0, wx.EXPAND)
        boxinput.Add(boxiccidtest, 0, wx.EXPAND)

        # printer
        sb = wx.StaticBox(self, -1, u('期望版面'))
        sbsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
        self.printer = PrinterPanel(sb)
        sbsizer.Add(self.printer, 0) #, wx.EXPAND|wx.ALL)
        boxinput.Add(sbsizer, 1, wx.EXPAND)

        # log window
        sb = wx.StaticBox(self, -1, u('检测日记'))
        sbsizer = wx.StaticBoxSizer(sb, wx.VERTICAL)
        self.log = wx.richtext.RichTextCtrl(sb, -1, '', size=(-1,-1), style=wx.TE_DONTWRAP|wx.HSCROLL|wx.VSCROLL|wx.TE_READONLY|wx.TE_MULTILINE)
        sbsizer.Add(self.log, 1, wx.EXPAND|wx.ALL)

        boxloginput = wx.BoxSizer(wx.HORIZONTAL)
        boxloginput.Add(sbsizer, 2, wx.EXPAND|wx.ALL)
        boxloginput.Add(boxinput, 1, wx.EXPAND|wx.ALL)


        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(boxloginput, 1, wx.EXPAND)

        # bind
        self.Bind(wx.EVT_COMBOBOX, self.OnSelectReader, self.readercombo)

        # finally
        self.SetSizer(box)
        self.GetBestSize()

    def prdCallback(self, event):
        value = event.GetString()
        if value:
            if os.path.isfile(value):
                history = self.prd.GetHistory()
                if value not in history:
                    history.append(value)
                    self.prd.SetHistory(history)

    def OnTest(self, event):
        ''' '''
        order, prd, iccid = utf8toascii(self.order.GetValue().strip()), self.prd.GetValue(), utf8toascii(self.iccid.GetValue().strip()).upper()
        if not os.path.isfile(prd):
            self.showmsg('不正确的prd数据文件', prd)
            return
        try:
            OrdernoValidator().test({'ORDERNO':order}, self.logger)
        except Exception as e:
            self.showmsg('不正确的订单号', order)
            return

        try:
            if len(iccid)==19:
                iccid1 = swap(iccid+'F')
            elif len(iccid)==20:
                iccid1 = swap(iccid)
            ICCIDValidator().test({'ICCID':iccid1}, self.logger)
        except Exception as e:
            self.showmsg('输入的ICCID格式不正确', iccid)
            return

        try:
            script = api_util.gettestscript(order)
        except Exception as e:
            self.error(traceback.format_exc(e))
            self.showmsg('获取检测脚本失败', order)
            return

        try:
            module = api_util.importmodule(script, order)
        except Exception as e:
            self.error(traceback.format_exc(e))
            self.showmsg('检测脚本无效', order)
            return

        message = u("测试中，请勿拔卡！")
        busy = PBI.PyBusyInfo(message, parent=None, title=u("测试中"))
        wx.Yield()
        
        try:
            passedno, warningno, errorno = api_util.testorder(module, order, prd, iccid1, self.printer)
        except Exception as e:
            self.error(traceback.format_exc(e))
            del busy
            self.showmsg('检测过程不正常结束。测试不通过！', order)
            return
        del busy

        if errorno == 0:
            if warningno == 0:
                self.showmsg('检测通过', order, style='')
            else:
                self.showmsg('检测通过。但发现 %d 个警告。' % warningno, order)
        else:
            self.showmsg('检测不通过：发现 %d 个错误、%d 个警告。'%(errorno, warningno), order)

    def OnReset(self, event):
        try:
            api_pcsc.reset()
            atr = api_pcsc.getatr()
            self.info('ATR: ' + atr)
        except Exception as e:
            self.showlongmsg('复位失败', str(e))
            return

    def OnSelectReader(self, event):
        name = str(self.readers[event.GetSelection()])
        self.info("尝试连接读卡器 '%s'" % name)
        try:
            api_pcsc.connectreader(name)
            atr = api_pcsc.getatr()
        except Exception as e:
            self.showlongmsg('读卡器连接失败', str(e))
            return
        self.info("ATR '%s'" % atr)



class SIMClientPanel(ClientPanel):

    SN_Label = 'ICCID'
    SN_Value = '8952020516692000313'

    def __init__(self, parent):
        # init
        ClientPanel.__init__(self, parent)

        self.initLogging()
        self.Bind(EVT_WX_LOG_EVENT, self.onLogEvent)


    def initLogging(self):
        root = logging.getLogger('')
        handler = wxLogHandler(self)
        FORMAT = u'%(relativeCreated)5d - %(asctime)s - %(levelname)s - %(name)s - %(message)s'
        handler.setFormatter(logging.Formatter(FORMAT))
        root.addHandler(handler)

    def onLogEvent(self, event):
        '''
        Add event.message to text window
        '''
        msg = event.message
        self.log.SetInsertionPointEnd()
        if event.levelno == logging.ERROR:
            self.log.BeginTextColour(wx.RED)
        elif event.levelno == logging.WARNING:
            self.log.BeginTextColour(wx.BLUE)
        else:
            self.log.BeginTextColour(wx.BLACK)
        self.log.WriteText(msg)
        self.log.EndTextColour()
        self.log.Newline()
        self.log.ShowPosition(self.log.GetLastPosition())
        event.Skip()


