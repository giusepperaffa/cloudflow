# ========================================
# Import Python Modules (Standard Library)
# ========================================
import collections
import re

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.utils.fileprocessingreslib import extract_dict_from_yaml
from cloudflow.pluginmodels.iamrolesperfunctionpluginreslib import IAMRolesPerFunctionPluginModelCls

# =======
# Classes
# =======
class PluginExtractedInfoCls:
    # === Constructor ===
    def __init__(self):
        """
        Class constructor. This class allows handling a data structure
        that stores plugin-specific information. An API is provided to
        facilitate the extraction of information. 
        """
        self.plugin_info = collections.defaultdict(dict)

    # === Method ===
    def get_config_params_for_plugin(self, plugin_name):
        """
        Method that returns the dictionary containing the
        configuration parameters extracted for the plugin
        specified as input argument. When an exception is
        raised the method returns None.
        NOTE: The plugin name is not processed by this method.
        This implies that the string specifying the plugin
        name must abide by the naming convention adopted
        to initialize the data structure.
        """
        try:
            return self.plugin_info['config'][plugin_name]
        except KeyError as e:
            print(f'--- Configuration parameters for plugin {plugin_name} not retrieved ---')
            print(f'--- The following key is not present in the plugin data structure: {e} ---')
            return None
        except Exception as e:
            print(f'--- Configuration parameters for plugin {plugin_name} not retrieved ---')
            print(f'--- {e} ---')
            return None

    # === Method ===
    def get_permissions_for_handler(self,
                                    handler_name,
                                    service_name=None,
                                    keep_service_name=True):
        """
        Method that returns the permissions for a specific
        handler as a set. Input parameters:
        -) handler_name: String specifying the handler name
        -) service_name: String specifying the cloud service
        name. If None, all the available permissions are
        returned, i.e., the service-related information is
        ignored.
        -) keep_service_name: Boolean flag. If True, the
        service name is kept with the actual permission
        name (e.g., dynamodb:GetItem), otherwise it is
        removed (e.g., GetItem).
        """
        try:
            # Extract permissions from data structure
            if service_name is not None:
                # The following set comprehension implements a filter by service name
                permissions = {permission for permission in self.plugin_info['handlers'][handler_name]
                            if permission.startswith(service_name)}
            else:
                permissions = self.plugin_info['handlers'][handler_name]
            # Post-process extracted permissions information
            if not keep_service_name:
                return {re.sub('^[a-zA-Z0-9]+:', '', permission) for permission in permissions}
            else:
                return permissions
        except KeyError as e:
            print(f'--- Permissions for handler {handler_name} not retrieved ---')
            print(f'--- The following key is not present in the plugin data structure: {e} ---')
            return None
        except Exception as e:
            print(f'--- Permissions for handler {handler_name} not retrieved ---')
            print(f'--- {e} ---')
            return None

    # === Method ===
    def has_config_params_for_plugin(self, plugin_name):
        """
        Method that returns True if the data structure includes
        configuration parameters for the specified plugin.
        NOTE: The plugin name is not processed by this method.
        This implies that the string specifying the plugin
        name must abide by the naming convention adopted
        to initialize the data structure.  
        """
        try:
            return plugin_name in self.plugin_info['config']
        except KeyError as e:
            # If no configuration-related information is stored,
            # an exception is raised.
            return False

    # === Method ===
    def has_handlers_permissions(self):
        """
        Method that returns True if the data structure includes 
        handler-level information, False otherwise.
        """
        return 'handlers' in self.plugin_info

    # === Method ===
    def store_config_params(self, plugin_name, config_params_dict):
        """
        Method that stores plugin-specific configuration parameters in
        the data structure handled by the class. The plugin input must
        be specified as a string. 
        """
        if config_params_dict is not None:
            self.plugin_info['config'][plugin_name] = config_params_dict

    # === Method ===
    def store_handlers_permissions(self, handlers_permissions_dict):
        """
        Method that stores handler-specific, permissions-related information
        in the data structure handled by the class. The input parameter is a
        dictionary structured as follows:
        -) Keys: String specifying the handler, e.g., 'func1'.
        -) Values: Set specifying the permissions for that handler, e.g.,
        {'dynamodb:GetItem'}
        """
        # Process handler-level permissions dictionary
        if handlers_permissions_dict is not None:
            for handler, permissions in handlers_permissions_dict.items():
                try:
                    self.plugin_info['handlers'][handler].update(permissions)
                except KeyError as e:
                    self.plugin_info['handlers'][handler] = permissions

class PluginManagerCls:
    # === Constructor ===
    def __init__(self, config_dict):
        """
        Class constructor. It expects to receive a dictionary that maps
        the Serverless Framework YAML configuration file.
        """
        # Attribute initialization
        self.config_dict = config_dict
        # Object with information extracted from the plugins
        self.plugin_extracted_info = PluginExtractedInfoCls()
        # Additional initialization steps
        self.init_plugin_models_dict()
        # Plugin processing
        self.process_all_plugins()

    # === Protected Method ===
    def _extract_configuration(self, plugin_model_obj):
        """
        Method that extracts and stores plugin-specific configuration
        parameters.
        """
        config_params_dict = plugin_model_obj.extract_configuration()
        plugin_name = plugin_model_obj.get_plugin_name()
        self.plugin_extracted_info.store_config_params(plugin_name, config_params_dict) 

    # === Protected Method ===
    def _extract_events(self, plugin_model_obj):
        """
        Method that extracts and stores events-specific information.
        """
        pass

    # === Method ===
    def _extract_handlers_permissions(self, plugin_model_obj):
        """
        Method that extracts and stores handlers-specific,
        permissions-related information.
        """
        # Extract handler-level permissions dictionary
        handlers_permissions_dict = plugin_model_obj.extract_handlers_permissions()
        self.plugin_extracted_info.store_handlers_permissions(handlers_permissions_dict)

    # === Method ===
    def _extract_services_permissions(self, plugin_model_obj):
        """
        Method that extracts and stores services-specific,
        permissions-related information.
        """
        pass

    # === Method ===
    def init_plugin_models_dict(self):
        """
        Method that initializes a dictionary that maps a plugin
        to a class that models that plugin. NOTE: When new
        plugin model classes are implemented, the dictionary
        initialization in this method has to be updated.
        """
        self.plugin_models_dict = dict()
        self.plugin_models_dict['serverless-iam-roles-per-function'] = IAMRolesPerFunctionPluginModelCls

    # === Method ===
    def process_all_plugins(self):
        """
        Method that initializes the plugin model objects, which
        are then used to extract plugin-specific information. 
        If a plugin detected in the configuration file is not
        supported, a warning message is printed. 
        """
        for plugin in self.config_dict['plugins']:
            try:
                print(f'--- Processing plugin: {plugin} ---')
                # Initialize plugin-specific model object
                plugin_model_obj = self.plugin_models_dict[plugin](self.config_dict)
                # Extract plugin-specific information
                self.process_plugin(plugin_model_obj)                
            except KeyError:
                print(f'--- WARNING: Plugin {plugin} not supported ---')

    # === Method ===
    def process_plugin(self, plugin_model_obj):
        """
        Method that extracts all the required information from
        the plugin model object passed as input argument.
        NOTE: This method relies on naming convention to identify
        the specific methods that implement the actual extraction
        of information.  
        """
        for flt_method in (method for method in dir(self) if method.startswith('_extract')):
            getattr(self, flt_method)(plugin_model_obj)
