from qgis.core import (
    Qgis,
    QgsCategorizedSymbolRenderer,
    QgsExpressionContextUtils,
    QgsGraduatedSymbolRenderer,
    QgsLayerTree,
    QgsMessageLog,
    QgsRuleBasedRenderer
)
from qgis.server import QgsServerFilter, QgsConfigCache, QgsServerSettings


class SplitCategorizedLayersFilter(QgsServerFilter):
    """QGIS Server SplitCategorizedLayers plugin."""

    def __init__(self, server_iface):
        super().__init__(server_iface)

    def onRequestReady(self):
        server_settings = QgsServerSettings()
        server_settings.load()
        QgsConfigCache.initialize(server_settings)
        config_cache = QgsConfigCache.instance()
        map_file = server_settings.projectFile()
        if not map_file:
            map_file = self.serverInterface().requestHandler().parameter("MAP")
        QgsMessageLog.logMessage(
            f"Converting {map_file}", "SplitCategorizedLayer", Qgis.MessageLevel.Info
        )

        qgs_project = config_cache.project(map_file)
        if qgs_project is None:
            QgsMessageLog.logMessage(
                "The requested project could not be read", "SplitCategorizedLayer", Qgis.MessageLevel.Critical
            )
            return True

        # Walk through layer tree, split categorized layers as required
        root = qgs_project.layerTreeRoot()
        # QgsMessageLog.logMessage(
        #     f"XXX Before = %s" % (root.dump()), "SplitCategorizedLayer", Qgis.MessageLevel.Info
        # )
        for (idx, child) in enumerate(root.children()):
            self.split_layers_in_tree(child, root, idx, qgs_project)
        # QgsMessageLog.logMessage(
        #     f"XXX After = %s" % (root.dump()), "SplitCategorizedLayer", Qgis.MessageLevel.Info
        # )
        return True

    def split_layers_in_tree(self, node, parent, pos, qgs_project):

        if QgsLayerTree.isLayer(node):
            layer = node.layer()
            context = QgsExpressionContextUtils.layerScope(layer)
            if (
                not layer.isValid()
                or not context.hasVariable("convert_categorized_layer")
                or context.variable("convert_categorized_layer").lower() != "true"
            ):
                return

            layerRenderer = layer.renderer()

            if isinstance(layerRenderer, QgsCategorizedSymbolRenderer):
                categories_list = layerRenderer.categories()
            elif isinstance(layerRenderer, QgsGraduatedSymbolRenderer):
                categories_list = layerRenderer.legendSymbolItems()
            elif isinstance(layerRenderer, QgsRuleBasedRenderer):
                categories_list = layerRenderer.rootRule().children()
            else:
                categories_list = []
            QgsMessageLog.logMessage(
                f"Spliting {layer.name()} into {len(categories_list)} layers",
                "SplitCategorizedLayer",
                Qgis.MessageLevel.Info,
            )

            group = parent.insertGroup(pos, layer.name())
            for category in categories_list:
                category_layer = layer.clone()
                category_layer.setTitle(category.label())
                category_layer.setName(category.label())
                category_layer.setShortName(category.label())
                category_layer.setCrs(layer.crs())
                QgsExpressionContextUtils.setLayerVariable(category_layer, "convert_categorized_layer", "false")

                cat_renderer = QgsRuleBasedRenderer.convertFromRenderer(layerRenderer)

                category_layer.setRenderer(cat_renderer)
                root_rule = category_layer.renderer().rootRule()
                for rule in root_rule.children():
                    if rule.label() != category.label():
                        root_rule.removeChild(rule)

                qgs_project.addMapLayer(category_layer, False)
                group.addLayer(category_layer)
            qgs_project.removeMapLayer(layer)

        else:
            for (idx, child) in enumerate(node.children()):
                self.split_layers_in_tree(child, node, idx, qgs_project)

class SplitCategorizedLayers:
    """
    Add support to split categorized layers into
    multiple layers.
    """

    def __init__(self, server_iface):
        """Register the filter"""
        split_categorized_layers = SplitCategorizedLayersFilter(server_iface)
        server_iface.registerFilter(split_categorized_layers)
