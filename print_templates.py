from qgis.core import *
from qgis.server import *

class PrintTemplatesFilter(QgsServerFilter):
    def __init__(self, serverIface):
        super(PrintTemplatesFilter, self).__init__(serverIface)
        
    def onRequestReady(self):
        return True
    
    def onResponseComplete(self):
        return True

class PrintTemplates:
    def __init__(self, serverIface):
        self.iface = serverIface
        serverIface.registerFilter(PrintTemplatesFilter(serverIface))
