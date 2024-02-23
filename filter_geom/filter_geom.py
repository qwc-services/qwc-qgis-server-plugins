from qgis.core import *
from qgis.server import *
from qgis.PyQt.QtCore import QFile, QIODevice
from qgis.PyQt.QtXml import QDomDocument
import os

class FilterGeomFilter(QgsServerFilter):
    def __init__(self, serverIface):
        super(FilterGeomFilter, self).__init__(serverIface)
        self.__layouts = []
        self.__project = None
        
    def onRequestReady(self):
        
        # Only apply FILTER_GEOM to GetMap and GetLegendGraphics. GetFeatureInfo already honours it
        request = self.serverInterface().requestHandler()
        requestParam = request.parameter('REQUEST').upper()
        filterGeomParam = request.parameter('FILTER_GEOM')
        filterParam = request.parameter('FILTER')
        layersParam = request.parameter('LAYERS').split(",")
        crsParam = request.parameter('CRS')
        srid = crsParam[5:]
        if not requestParam in ['GETMAP', 'GETLEGENDGRAPHICS'] or not filterGeomParam:
            return True

        # Inject st_intersects and st_geomfromtext tokens if necessary
        extraTokens = [token.lower() for token in filter(bool, os.getenv("QGIS_SERVER_ALLOWED_EXTRA_SQL_TOKENS", "").split(","))]
        changed = False
        for token in ["st_intersects", "st_geomfromtext"]:
            if not token in extraTokens:
                extraTokens.append(token)
                changed = True
        if changed:
            os.putenv("QGIS_SERVER_ALLOWED_EXTRA_SQL_TOKENS", ",".join(extraTokens))
            # self.serverInterface().reloadSettings()
            # QgsMessageLog.logMessage(
            #     f"XXX Altered QGIS_SERVER_ALLOWED_EXTRA_SQL_TOKENS to %s" % (",".join(extraTokens)), "FilterGeom", Qgis.MessageLevel.Info
            # )

        projectPath = self.serverInterface().configFilePath()
        project = QgsConfigCache.instance().project(projectPath)
        filters = dict(map(lambda entry: entry.split(":"), filter(bool, filterParam.split(";"))))

        # Append geometry filter expression to all postgis layers
        for layer in project.mapLayers().values():

            layername = layer.shortName()
            if QgsServerProjectUtils.wmsUseLayerIds(project):
                layername = layer.id()
            elif not layername:
                layername = layer.name()

            if not layername in layersParam:
                continue

            filterExpr = None
            if layer.providerType() == "postgres":
                geomColumn = QgsDataSourceUri(layer.source()).geometryColumn()
                filterExpr = "ST_Intersects ( \"%s\" , ST_GeomFromText ( '%s' , %s ) )" % (geomColumn, filterGeomParam, srid)

            if filterExpr:
                if layername in filters:
                    filters[layername] += "AND " + filterExpr
                else:
                    filters[layername] = filterExpr

                # QgsMessageLog.logMessage(
                #     f"XXX New filter for %s = %s" % (layername, filters[layername]), "FilterGeom", Qgis.MessageLevel.Info
                # )

        request.setParameter('FILTER', ";".join(map(lambda entry: ":".join(entry), filters.items())))
        return True

class FilterGeom:
    def __init__(self, serverIface):
        self.iface = serverIface
        serverIface.registerFilter(FilterGeomFilter(serverIface))
