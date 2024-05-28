# ========================================
# Import Python Modules (Project-specific)
# ========================================
from cloudflow.modules.customresolverreslib import check_if_resolved, resolve_value_from_yaml

# =======
# Classes
# =======
class EnvInspectionManagerCls:
    # === Constructor ===
    def __init__(self,
                 infrastruc_code_dict,
                 handler_name,
                 sc_file):
        """
        Class constructor. Input arguments:
        -) infrastruc_code_dict: Dictionary that maps the infrastructure
        code (i.e., the YAML file) of the application under test.
        -) handler_name: String specifying an application handler. It
        is used to specify its specific environment, if any.
        -) sc_file: String specifying the full path of the source code
        file to be processed.
        """
        # Initialize attributes (from input arguments)
        self.infrastruc_code_dict = infrastruc_code_dict
        self.handler_name = handler_name
        self.sc_file = sc_file
        # Auxiliary instance variables
        self.handler_info = self.infrastruc_code_dict['functions'][self.handler_name]

    # === Protected Method ===
    def _inspect_handler_level_env(self, env_var):
        """
        Method that processes the handler-level environment,
        if any. If an exception is raised, it returns None
        (e.g, there is no handler-level environment).
        """
        try:
            extracted_value = str(self.handler_info['environment'][env_var])
            return self._process_env_var_value(extracted_value)
        except:
            return

    # === Protected Method ===
    def _inspect_provider_level_env(self, env_var):
        """
        Method that processes the provider-level environment,
        if any. If an exception is raised, it returns None
        (e.g, there is no provider-level environment).
        NOTE: The provider-level environment is shared among
        multiple handlers. More information available at:
        https://www.serverless.com/framework/docs-providers-aws-guide-functions
        """
        try:
            extracted_value = str(self.infrastruc_code_dict['provider']['environment'][env_var])
            return self._process_env_var_value(extracted_value)
        except:
            return

    # === Protected Method ===
    def _process_env_var_value(self, env_var_value):
        """
        Method that processes a candidate value for an
        environment value. If needed, it attempts to
        resolve the value, and returns it only if fully
        resolved. None is returned otherwise.
        """
        # Check if the extracted value is not fully resolved 
        if not check_if_resolved(env_var_value):
            env_var_value = resolve_value_from_yaml(env_var_value, self.infrastruc_code_dict)
        # Return a string only if it is detected as fully resolved
        return (env_var_value if check_if_resolved(env_var_value) else None)

    # === Method ===
    def get_env_var_value(self, env_var):
        """
        Method that returns the value for the environment
        variable env_var (to be specified as string). The
        code first inspects the handler-level environment
        (if any), and then the provider-level environment
        (if any).
        NOTE: If the specified environment variable does
        not exist or the retrieved valued is not fully
        resolved, the method returns None.
        """
        extracted_value = self._inspect_handler_level_env(env_var)
        if extracted_value is not None:
            return extracted_value
        else:
            return self._inspect_provider_level_env(env_var)
