# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.pluginmodels.pluginmodelssharedreslib import PluginModelCls 

# =======
# Classes
# =======
class IAMRolesPerFunctionPluginModelCls(PluginModelCls):
    # === Constructor ===
    def __init__(self, config_dict):
        """
        Class constructor. It expects to receive a dictionary that maps
        the Serverless Framework YAML configuration file.
        """
        # Attribute initialization
        self.config_dict = config_dict
        # Extract override configuration
        self._get_override_config()

    # === Protected Method ===
    def _get_override_config(self):
        """
        Method that initializes an instance variable that
        stores in a Boolean the override configuration of
        the plugin.
        """
        try:
            # The plugin documentation explains that a defaultInherit tag
            # can be used to change the default behaviour of the plugin.
            # For more detailed information, refer to the plugin documentation:
            # https://www.serverless.com/plugins/serverless-iam-roles-per-function
            extracted_val = self.config_dict['custom']['serverless-iam-roles-per-function']['defaultInherit']
            # Negation is necessary because the method returns a boolean
            # flag that specifies whether override is set up
            self.override_config = not eval(extracted_val.capitalize())
        except:
            # Default behaviour of the plugin, as per documentation
            self.override_config = True 

    # === Method ===
    def extract_configuration(self):
        """
        Method that extracts plugin-specific configuration parameters.
        The method returns a dictionary structured as follows:
        -) Keys: String specifying the parameter name
        -) Values: Value(s) for the parameter specified in the key 
        """
        handlers_override_config_set = set()
        # Process all the handlers in the configuration file
        for handler in self.config_dict['functions']:
            try:
                # Retrieve handler-specific override configuration
                handler_override_config = self.config_dict['functions'][handler]['iamRoleStatementsInherit']
                # Negation is necessary because the data structure
                # being populated specified the override configuration
                handlers_override_config_set.add((handler, not eval(handler_override_config.capitalize())))
            except:
                handlers_override_config_set.add((handler, self.override_config))
        return {'Override': handlers_override_config_set}     
    
    # === Method ===
    def extract_handlers_permissions(self):
        """
        Method that extracts permissions on a per handler basis.
        """
        # Initialize returned data structure
        handlers_perm_dict = dict()
        # Process all the handlers in the configuration file
        for handler in self.config_dict['functions']:
            print(f'--- Processing handler: {handler} ---')
            try:
                # Retrieve handler-specific permission dictionary
                handler_perm_dict = self.config_dict['functions'][handler]['iamRoleStatements'][0]
                # Initialize handler-specific returned dictionary entry 
                if handler_perm_dict['Effect'] == 'Allow':
                    handlers_perm_dict[handler] = set(handler_perm_dict['Action'])
            except:
                pass
        return handlers_perm_dict

    # === Method ===
    def extract_perm_res_dict(self):
        """
        Method that extracts the permission-resource
        dictionary for each handler.
        NOTE: The returned data structure is a nested
        dictionary, because each handler can have a
        different permission-resource dictionary.
        """
        # Initialize returned data structure
        perm_res_dict = dict()
        # Process all the handlers in the configuration file
        for handler in self.config_dict['functions']:
            print(f'--- Extracting permission-resource dictionary for handler: {handler} ---')
            try:
                # Retrieve handler-specific permission dictionary
                handler_perm_dict = self.config_dict['functions'][handler]['iamRoleStatements'][0]
                # Initialize handler-specific returned dictionary entry
                if handler_perm_dict['Effect'] == 'Allow':
                    # Generator object to split the cloud service from
                    # the actual permission. Both pieces of information
                    # are returned in a tuple.
                    service_perm_gen_obj = ((perm.split(':')[0].strip(), perm.split(':')[1].strip())
                                            for perm in handler_perm_dict['Action'])
                    perm_res_dict[handler] = {str(handler_perm_dict['Resource']): {service_perm for service_perm
                                                                                   in service_perm_gen_obj}}
            except:
                pass
        return perm_res_dict
