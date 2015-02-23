#! /usr/bin/env python
"""
SYNOPSIS
    Small media ingest/prep program

    run on directory containing media (in raw-media or in jpg)

AUTHOR
    Noah Hafner <nmh+misc2013@nomh.org>
    ref:    http://code.activestate.com/recipes/528877/ (Noah Spurrier)

LICENSE
    This program is available under the Apache Artistic license
    Copyright Noah Hafner 2010-2013

VERSION
    2
"""
#refs:
#* http://www.pha.com.au/kb/index.php/Python_Skeleton_Scripts
#* http://stackoverflow.com/questions/2387272/\
#        what-is-the-best-python-library-module-skeleton-code
#* https://github.com/ctb/SomePackage
#* http://pypi.python.org/pypi/skeleton/0.4
#* http://www.blog.pythonlibrary.org/2010/10/28/\
#        wxpython-an-xrced-tutorial/comment-page-1/

#import argparse
#import hashlib
#import logging
import os
#import re
#import subprocess
import sys
#import time
import traceback
import wx
from wx import xrc
# XRCed stub class
import gui_xrc


class appFrame(gui_xrc.xrcappFrame):
    """add functionality to xrc autogenerated stub"""
    def __init__(self):
        """Constructor"""
        gui_xrc.xrcappFrame.__init__(self, parent=None)
        self.Show()

    def OnMenu_new(self, evt):
        # Replace with event handler code
        print "OnMenu_new()"

    def OnMenu_open(self, evt):
        # Replace with event handler code
        print "OnMenu_open()"

    def OnMenu_save(self, evt):
        # Replace with event handler code
        print "OnMenu_save()"

    def OnMenu_saveAs(self, evt):
        # Replace with event handler code
        print "OnMenu_saveAs()"

    def OnMenu_exit(self, evt):
        # Replace with event handler code
        print "OnMenu_exit()"

    def OnTool_tbSaveAs(self, evt):
        # Replace with event handler code
        print "OnTool_tbSaveAs()"

    def OnTool_tbNew(self, evt):
        # Replace with event handler code
        print "OnTool_tbNew()"

    def OnTool_tbSave(self, evt):
        # Replace with event handler code
        print "OnTool_tbSave()"


class exApp(wx.App):
    def OnInit(self):
        self.res = xrc.XmlResource("gui.xrc")

        self.frame = appFrame()

        return True


def main():
    app = exApp(0)
    app.MainLoop()

if __name__ == '__main__' or __name__ == sys.argv[0]:
    try:
        sys.exit(main())
    except KeyboardInterrupt, e:
        print "break, %s" % str(e)
    except SystemExit, e:  # sys.exit()
        raise e
    except Exception, e:
        print 'ERROR, UNEXPECTED EXCEPTION'
        print str(e)
        traceback.print_exc()
        os._exit(1)