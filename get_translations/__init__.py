from .get_translations import GetTranslations


def serverClassFactory(serverIface):
    return GetTranslations(serverIface)
