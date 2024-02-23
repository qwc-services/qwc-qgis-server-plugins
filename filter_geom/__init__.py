from .filter_geom import FilterGeom


def serverClassFactory(serverIface):
    return FilterGeom(serverIface)
