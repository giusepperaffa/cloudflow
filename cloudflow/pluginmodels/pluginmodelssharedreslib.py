# =====================
# Import Python Modules
# =====================
import re

# =======
# Classes
# =======
class PluginModelCls:
    # === Method ===
    def extract_configuration(self):
        """
        Method to be further specialized in the derived
        plugin model class, if relevant to the plugin.
        """
        return

    # === Method ===
    def extract_events(self):
        """
        Method to be further specialized in the derived
        plugin model class, if relevant to the plugin.
        """
        return

    # === Method ===
    def extract_handlers_permissions(self):
        """
        Method to be further specialized in the derived
        plugin model class, if relevant to the plugin.
        """
        return

    # === Method ===
    def extract_perm_res_dict(self):
        """
        Method to be further specialized in the derived
        plugin model class, if relevant to the plugin.
        """
        return

    # === Method ===
    def extract_services_permissions(self):
        """
        Method to be further specialized in the derived
        plugin model class, if relevant to the plugin.
        """
        return

    # === Method ===
    def get_plugin_name(self):
        """
        Method that returns the plugin name as a string.
        NOTE: A naming convention that relies on the plugin
        model class name is used.
        """
        return re.sub('PluginModelCls$', '', self.__class__.__name__) 
