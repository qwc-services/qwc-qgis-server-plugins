from qgis.core import *
from qgis.server import *
from qgis.PyQt.QtCore import QFile, QIODevice
from qgis.PyQt.QtXml import QDomDocument
import os

class PrintTemplatesFilter(QgsServerFilter):
    def __init__(self, serverIface):
        super(PrintTemplatesFilter, self).__init__(serverIface)
        self.__layouts = []
        
    def onRequestReady(self):
        projectPath = self.serverInterface().configFilePath()
        self.__project = QgsConfigCache.instance().project( projectPath )
        
        #Read all the layouts in PRINT_LAYOUT_DIR and insert it to the current project
        if 'PRINT_LAYOUT_DIR' in os.environ:
            layoutDir = os.environ['PRINT_LAYOUT_DIR']
            for f in os.listdir(layoutDir):
                print(f)
                layoutFile = QFile(os.path.join(layoutDir,f))
                if not layoutFile.open( QIODevice.ReadOnly ):
                    QgsMessageLog.logMessage('Opening file failed', 'plugin', Qgis.Critical)
                    continue
                domDoc = QDomDocument()
                if not domDoc.setContent(layoutFile):
                    QgsMessageLog.logMessage('Reading xml document failed', 'plugin', Qgis.Critical)
                    continue
                layout = QgsPrintLayout(self.__project)
                if not layout.readXml( domDoc.documentElement(), domDoc, QgsReadWriteContext() ):
                    QgsMessageLog.logMessage('Reading layout failed', 'plugin', Qgis.Critical)
                else:
                    QgsMessageLog.logMessage('Reading of layout was successfull', 'plugin', Qgis.Critical)
                    
                if not self.__project.layoutManager().addLayout(layout):
                    QgsMessageLog.logMessage('Could not add layout to project', 'plugin', Qgis.Critical)
                    
                self.__layouts.append(layout)
        
        return True
    
    def onResponseComplete(self):
        for layout in self.__layouts:
            self.__project.layoutManager().removeLayout(layout)
            
        self.__layouts.clear()
        
        return True

class PrintTemplates:
    def __init__(self, serverIface):
        self.iface = serverIface
        serverIface.registerFilter(PrintTemplatesFilter(serverIface))
