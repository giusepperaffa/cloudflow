# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast
import re

# ========================================
# Import Python Modules (Project-specific)
# ========================================
from cloudflow.modules.customresolverreslib import check_if_resolved, resolve_value_from_yaml

# =========
# Functions
# =========
def detect_os_environ_ast_node(subscript_node):
    """
    Function that processes an ast.Subscript node and
    returns True if it is an os.environ node (False
    otherwise).
    """
    return all([subscript_node.value.value.id == 'os',
                subscript_node.value.attr == 'environ'])

def detect_os_getenv_ast_node(call_node):
    """
    Function that processes an ast.Call node and
    returns True if it is an os.getenv node (False
    otherwise).
    """
    return all([call_node.func.value.id == 'os',
                call_node.func.attr == 'getenv'])

def inspect_ast_node(ast_node,
                     infrastruc_code_dict,
                     handler_name,
                     sc_file):
    """
    Function that processes the AST node passed as input argument
    and returns its resolved value after inspecting the environment
    variables. The function supports only these cases:
    1) AST node with os.environ
    2) AST node with os.getenv
    3) AST node with variable name
    In all other cases, the function returns None.
    """
    # Object used to inspect environment variables
    env_inspection_manager = EnvInspectionManagerCls(infrastruc_code_dict,
                                                     handler_name,
                                                     sc_file)
    # -----------------------------------------------
    # CASE 1 - Inspected AST node includes os.environ
    # -----------------------------------------------
    if isinstance(ast_node, ast.Subscript) and detect_os_environ_ast_node(ast_node):
        env_var = ast_node.slice.value.value
        return env_inspection_manager.get_env_var_value(env_var)
    # ----------------------------------------------
    # CASE 2 - Inspected AST node includes os.getenv
    # ----------------------------------------------
    elif isinstance(ast_node, ast.Call) and detect_os_getenv_ast_node(ast_node):
        env_var = ast_node.args[0].value
        return env_inspection_manager.get_env_var_value(env_var)
    # ---------------------------------------------
    # CASE 3 - Inspected AST node includes variable
    # ---------------------------------------------
    elif isinstance(ast_node, ast.Name):
        return env_inspection_manager.get_var_value_from_env(ast_node.id)

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
        self.handler_info = self.infrastruc_code_dict['functions'].get(self.handler_name)

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
            try:
                return self._inspect_unres_info(str(self.handler_info['environment']), env_var)
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
            try:
                return self._inspect_unres_info(str(self.infrastruc_code_dict['provider']['environment']), env_var)
            except:
                return

    # === Protected Method ===
    def _inspect_unres_info(self, env_info, env_var):
        """
        Method that processes unresolved information about
        an environment. This method supports the case when
        a YAML file environment tag identifies a different
        section of the file, e.g.:
        -) ${self:custom.settings}
        If the processing is unsuccessful, returns None.
        """
        if not check_if_resolved(env_info):
            try:
                unres_val_reg_exp = re.compile(r'\$\{self:([\w\-\.]+)\}')
                for index, key in enumerate(unres_val_reg_exp.search(env_info).group(1).split('.')):
                    if index == 0:
                        aux_var = self.infrastruc_code_dict[key]
                    else:
                        aux_var = aux_var[key]
                return aux_var[env_var]
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

    # === Method ===
    def get_var_value_from_env(self, var):
        """
        Method that returns the value for the source code
        variable var (to be specified as string), obtained
        from the inspection of the handler-level or the
        provider-level environment. In the following cases:
        -) Input variable assignment not found in the code
        -) Environment variable not found
        -) Environment variable not fully resolved
        the code returns None.
        NOTE: This method only supports simple assignments
        implemented with os.environ and os.getenv. Examples:
        -) kms_key_alias = os.environ['KMS_KEY_ALIAS']
        -) region = os.getenv('REGION')
        """
        with open(self.sc_file, mode='r') as sc_file_obj:
            # Create in-memory data structure
            ast_tree = ast.parse(sc_file_obj.read())
            # Identify ast.Assign nodes to be processed. These have as
            # a target (i.e., on the left hand-side of the assignment)
            # the variable specified as method input argument.
            for assign_node in (node for node in ast.walk(ast_tree)
                                if isinstance(node, ast.Assign) and node.targets[0].id == var):
                # ------------------------------------------------------
                # CASE 1 - Assignment implemented with os.environ, e.g.:
                # kms_key_alias = os.environ['KMS_KEY_ALIAS']
                # ------------------------------------------------------
                if isinstance(assign_node.value, ast.Subscript):
                    # Create handle to ast.Subscript instance for readability,
                    # and check if the assignment is implemented as expected.
                    subscript_node = assign_node.value
                    if detect_os_environ_ast_node(subscript_node):
                        env_var = subscript_node.slice.value.value
                        return self.get_env_var_value(env_var)
                # -----------------------------------------------------
                # CASE 2 - Assignment implemented with os.getenv, e.g.:
                # region = os.getenv('REGION')
                # -----------------------------------------------------
                elif isinstance(assign_node.value, ast.Call):
                    # Create handle to ast.Call instance for readability,
                    # and check if assignment is implemented as expected.
                    call_node = assign_node.value
                    if detect_os_getenv_ast_node(call_node):
                        env_var = call_node.args[0].value
                        return self.get_env_var_value(env_var)
