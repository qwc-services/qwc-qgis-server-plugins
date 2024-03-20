from .wms_geotiff_output import WMSGeotiffOutput


def serverClassFactory(serverIface):
    return WMSGeotiffOutput(serverIface)
