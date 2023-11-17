from .print_templates import PrintTemplates


def serverClassFactory(serverIface):
    return PrintTemplates(serverIface)
