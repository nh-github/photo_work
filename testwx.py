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


class AppFrame(wx.Frame):
    """TODO: Needed?"""
    def __init__(self):
        #wx.Frame.__init__(self, None, -1, 'AppFrame',
        wx.Frame.__init__(self, None, -1, 'Hello World',
                          size=(550, 350))
        self.SetBackgroundColour(wx.NamedColour("WHITE"))


class exApp(wx.App):
    def OnInit(self):
        self.res = xrc.XmlResource("gui.xrc")

        self.frame = self.res.LoadFrame(None, 'appFrame')

        self.frame.Show()
        return True


class App(wx.App):
    """handles the event loop"""

    def OnInit(self):
        """Create and present app window"""
        frame = AppFrame()
        frame.Show(True)

        return True


def main():
    app = exApp(0)
    app.MainLoop()
    print "early exit!"
    sys.exit(0)
    print "foo!"
    app = App(0)
    app.MainLoop()
    #setup() #parse parameters, config, log

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
