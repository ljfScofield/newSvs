#!/usr/env python
# -*- coding: utf-8 -*-

import wx

import api_util
import ui_notebook_cos
import ui_notebook_sim

#----------------------------------------------------------------------
# define API
u = api_util.u

#----------------------------------------------------------------------

class TestNB(wx.Notebook):
    def __init__(self, parent, id, log):
        wx.Notebook.__init__(self, parent, id, style=wx.BK_DEFAULT)
        self.log = log

        # layout
        self.AddPage(ui_notebook_cos.ClientPanel(self), ui_notebook_cos.TITLE)
        self.AddPage(ui_notebook_sim.ClientPanel(self), ui_notebook_sim.TITLE)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(box)
        self.GetBestSize()


#----------------------------------------------------------------------



def runTest(frame, nb, log):
    win = TestNB(nb, -1, log)
    return win

#----------------------------------------------------------------------


overview = """<html><body>
<h2>Welcome to http://china-xinghan.com/</h2>
<font face="verdana">

</font>
</body></html>
"""



if __name__ == '__main__':
    import sys,os
    import run
    run.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])

