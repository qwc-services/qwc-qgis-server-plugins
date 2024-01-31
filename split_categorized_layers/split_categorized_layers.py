from qgis.core import (
    Qgis,
    QgsRuleBasedRenderer,
    QgsMessageLog,
    QgsCategorizedSymbolRenderer,
    QgsExpressionContextUtils,
    QgsGraduatedSymbolRenderer,
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
            f"Converting {map_file}",
            "SplitCategorizedLayer",
            Qgis.MessageLevel.Info,
        )
        self.split_layers_in_project(config_cache, map_file)
        return True

    def split_layers_in_project(self, config_cache: QgsConfigCache, project_path: str):
        qgs_project = config_cache.project(project_path)
        if qgs_project is None:
            QgsMessageLog.logMessage(
                "The requested project could not be read",
                "SplitCategorizedLayer",
                Qgis.MessageLevel.Critical,
            )
            return

        layer_order = []
        layers = []
        layer_tree_root = qgs_project.layerTreeRoot()

        for _layer in layer_tree_root.children():
            layer_order.append(_layer.name())

        for layer in qgs_project.mapLayers().values():
            context = QgsExpressionContextUtils.layerScope(layer)
            if (
                context.hasVariable("convert_categorized_layer")
                and context.variable("convert_categorized_layer").lower() == "true"
            ):
                layers.append(layer.name())

        for layer_name in layers:
            # Search for layer by name
            base_layer = qgs_project.layerStore().mapLayersByName(layer_name)[0]
            if not base_layer.isValid():
                continue

            # This is the layer that will be splitted into multiple layers
            base_layer_renderer = base_layer.renderer()

            if base_layer.name() not in layer_order:
                continue

            group_index = layer_order.index(base_layer.name())
            group = layer_tree_root.insertGroup(group_index, base_layer.name())

            if isinstance(base_layer_renderer, QgsCategorizedSymbolRenderer):
                categories_list = base_layer_renderer.categories()
            elif isinstance(base_layer_renderer, QgsGraduatedSymbolRenderer):
                categories_list = base_layer_renderer.legendSymbolItems()
            elif isinstance(base_layer_renderer, QgsRuleBasedRenderer):
                categories_list = base_layer_renderer.rootRule().children()
            else:
                categories_list = []
            QgsMessageLog.logMessage(
                f"Spliting {layer_name} into {len(categories_list)} layers",
                "SplitCategorizedLayer",
                Qgis.MessageLevel.Info,
            )

            for category in categories_list:
                category_layer = base_layer.clone()
                category_layer.setTitle(category.label())
                category_layer.setName(category.label())
                category_layer.setShortName(category.label())
                category_layer.setCrs(base_layer.crs())

                new_renderer = QgsRuleBasedRenderer.convertFromRenderer(
                    base_layer.renderer()
                )

                category_layer.setRenderer(new_renderer)
                root_rule = category_layer.renderer().rootRule()
                for rule in root_rule.children():
                    if rule.label() != category.label():
                        root_rule.removeChild(rule)

                qgs_project.addMapLayer(category_layer, False)
                group.addLayer(category_layer)
            qgs_project.removeMapLayer(base_layer)


class SplitCategorizedLayers:
    """
    Add support to split categorized layers into
    multiple layers.
    """

    def __init__(self, server_iface):
        """Register the filter"""
        split_categorized_layers = SplitCategorizedLayersFilter(server_iface)
        server_iface.registerFilter(split_categorized_layers)
