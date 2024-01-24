# -*- coding: utf-8 -*-
#thx to MNASR
from Components.Converter.Converter import Converter
from Components.Converter.Poll import Poll
from enigma import eConsoleAppContainer
import os, re, socket

class BlueA_myIP(Poll, Converter):
    
    IPLOCAL = 0

    def __init__(self, type):
        Converter.__init__(self, type)
        Poll.__init__(self)      
        if 'Iplocal' in type:
            self.type = self.IPLOCAL       
           
    def getText(self):       
        if self.type == self.IPLOCAL:
            gw = os.popen("ip -4 route show default").read().split()
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((gw[2], 0))
            ipaddr = s.getsockname()[0]
        return "%s" % ipaddr     

    text = property(getText)
   