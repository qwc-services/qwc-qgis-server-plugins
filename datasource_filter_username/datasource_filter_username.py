#
# Copyright (c) 2025 Sandro Mani, Sourcepole AG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from qgis.core import *
from qgis.server import *

class DatasourceFilterUsernameFilter(QgsServerFilter):
    def __init__(self, serverIface):
        super(DatasourceFilterUsernameFilter, self).__init__(serverIface)
        self.__layouts = []
        self.__project = None
        
    def onRequestReady(self):
        
        request = self.serverInterface().requestHandler()
        username = request.parameter('QWC_USERNAME')
        QgsMessageLog.logMessage('Got QWC_USERNAME=%s' % (username), "[DatasourceFilterUsername]", Qgis.Info)

        if not username:
            return True

        projectPath = self.serverInterface().configFilePath()
        project = QgsConfigCache.instance().project(projectPath)
        for layer in project.mapLayers().values():
            if layer.providerType() != "postgres":
                continue

            subset = layer.subsetString()
            if subset:
                layer.setSubsetString(subset.replace("$QWC_USERNAME$", username))
                QgsMessageLog.logMessage('Replaced $QWC_USERNAME$ with %s in layer "%s" subset filter' % (username, layer.name()), "[DatasourceFilterUsername]", Qgis.Info)

        return True


class DatasourceFilterUsername:
    def __init__(self, serverIface):
        self.iface = serverIface
        serverIface.registerFilter(DatasourceFilterUsernameFilter(serverIface))
