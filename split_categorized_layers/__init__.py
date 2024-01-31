from .split_categorized_layers import SplitCategorizedLayers


def serverClassFactory(server_iface):
    return SplitCategorizedLayers(server_iface)
