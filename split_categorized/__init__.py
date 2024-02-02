from .split_categorized import SplitCategorizedLayers


def serverClassFactory(serverIface):
    return SplitCategorizedLayers(serverIface)
