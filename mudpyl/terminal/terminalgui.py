from twisted.internet.task import LoopingCall
from datetime import datetime, timedelta
import traceback
import gtk
import re
import sys
import threading
from twisted.internet.stdio import StandardIO
from twisted.internet import stdio, reactor
from twisted.protocols import basic
from twisted.web import client



class TerminalGUI(basic.LineReceiver):
    delimiter = '\n'
    def __init__(self, realm):
        self.realm = realm
        self.realm.addProtocol(self)
        realm.factory.gui = self

    def connectionMade(self):
        print 'TerminalGUI: Connection made'

    def connectionLost(self, reason = None):
        print 'Connection lost', reason
        reactor.stop()
        
    def metalineReceived(self, metaline):
        print sys.stdout.write(metaline.line)
    
    def lineReceived(self, line):
        print line
        self.realm.receive_gui_line(line)
    
    
def configure(factory):
    """Set the right reactor up and get the GUI going."""
    #from twisted.internet import selectreactor
    #reactor.install()

    gui = TerminalGUI(factory.realm)
    stdio.StandardIO(gui)
    #gui.start()


