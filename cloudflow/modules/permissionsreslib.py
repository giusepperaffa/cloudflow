# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast
import collections

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.utils.customprintreslib import print_table
from cloudflow.utils.awsarnprocessingreslib import AWSARNManagerCls
from cloudflow.modules.customresolverreslib import resolve_value_from_yaml, check_if_resolved
from cloudflow.modules.envinspectionreslib import inspect_ast_node
from cloudflow.utils.astprocessingreslib import get_call_input_ast_node

# =========
# Functions
# =========
def analyse_api_permissions(required_api_permissions,
                            service_permissions,
                            service_name,
                            plugin_info,
                            handler_name):
    """
    Function that determines whether an API call is allowed,
    and returns a Boolean (True => API call allowed, False
    => API call not allowed). The following input arguments
    are analysed:
    -) required_api_permissions: Set storing the permissions
    required for a given API call.
    -) service_permissions: Set storing the permissions that
    the relevant cloud service has. This information is
    extracted from the infrastructure code file.
    -) service_name: Input specifying as a string the name
    of the relevant cloud service.
    -) plugin_info: Instance of the class holding
    the information extracted by using the plugin models.
    -) handler_name: Input specifying as a string the name
    of the handler that includes the API call. If this input
    is set to None, no handler-level information is processed.
    """
    if plugin_info.is_empty() or (handler_name is None):
        # The analysis is based exclusively on the permissions required
        # for the API call and those extracted from the infrastructure
        # code. If the intersection between the required permissions and
        # those specified in the repository infrastructure code YAML file
        # is a non-empty set, then the execution of the API is allowed.
        return (required_api_permissions & service_permissions) != set([])
    elif plugin_info.has_handlers_permissions():
        print('--- Analysing handler-level permissions-related information... ---')
        if not plugin_info.has_config_params_for_plugin('IAMRolesPerFunction'):
            # NOTE: No configuration-related information about the plugin
            # serverless-iam-roles-per-function is available. As an
            # APPROXIMATION, the code considers the API call as allowed
            # if EITHER the permissions for the service OR the permissions
            # at handler-level include the permissions required for API.
            service_result = (required_api_permissions & service_permissions) != set([])
            handler_permissions = plugin_info.get_permissions_for_handler(handler_name,
                                                                          service_name,
                                                                          False)
            handler_result = (required_api_permissions & handler_permissions) != set([])
            return service_result or handler_result
        # If the execution reaches this point, the plugin-specific data
        # structure holds both configuration-related information about
        # the plugin serverless-iam-roles-per-function and handler-level
        # permissions-related information. As an APPROXIMATION, the code
        # considers exclusively the logic implemented by the plugin
        # serverless-iam-roles-per-function.
        elif [value for handler, value in plugin_info.get_config_params_for_plugin('IAMRolesPerFunction')['Override']
              if handler == handler_name][0]:
            # The override behaviour of the plugin serverless-iam-roles-per-function
            # is enabled. The required API permissions are compared only with the
            # handler-level permissions.
            handler_permissions = plugin_info.get_permissions_for_handler(handler_name,
                                                                          service_name,
                                                                          False)
            return (required_api_permissions & handler_permissions) != set([])
        else:
            # The override behaviour of the plugin serverless-iam-roles-per-function
            # is disabled. The required API permissions are compared with the union
            # of the permissions for the service and the handler-level permissions.
            handler_permissions = plugin_info.get_permissions_for_handler(handler_name,
                                                                          service_name,
                                                                          False)
            union_permissions = service_permissions | handler_permissions
            return (required_api_permissions & union_permissions) != set([])
    elif plugin_info.has_config_params_for_plugin('IAMRolesPerFunction'):
        # APPROXIMATION: The plugin-specific data structure does not have any
        # handler-related information, but it contains configuration-related
        # information about the plugin serverless-iam-roles-per-function. As
        # explained in the plugin documentation, in this very specific case
        # the handler acquires by default permissions to create and write to
        # CloudWatch logs, stream events and VPC. Even though some stream events
        # are of interest (e.g., those for DynamoDB), the others are currently
        # out of the scope of this project. As a result, the implementation
        # assumes that the handler has no permissions of any kind.
        return False
    else:
        # APPROXIMATION: When none of the above cases is detected, then
        # only the permissions for the cloud service are considered.
        # To be reviewed when additional plugins are supported.
        return (required_api_permissions & service_permissions) != set([])

def analyse_resource_level_permissions(required_api_permissions,
                                       perm_res_dict,
                                       service_name,
                                       resources_info,
                                       api_call_ast_node,
                                       infrastruc_code_dict,
                                       handler_name,
                                       sc_file):
    """
    Function that determines whether an API call is allowed
    by comparing the resource-level permissions with the
    resource-related API input arguments. The function returns
    a Boolean (True => API call allowed, False => API call not
    allowed). NOTE: To minimize false negatives, the function
    assumes that the required permissions are available when
    there is not enough information to establish otherwise.
    Therefore, it should be used along with the analysis code
    that assesses whether the same API call is allowed on the
    basis of the service-specific permissions.
    The following input arguments are analysed:
    -) required_api_permissions: Set storing the permissions
    required for a given API call.
    -) perm_res_dict: Dictionary with permissions-related
    information for resources explicitly specified in the
    YAML file. It can be obtained with one of the methods
    of the PermissionsIdentifierCls class.
    -) service_name: Input specifying as a string the name
    of the relevant cloud service.
    -) resources_info: Data structure with the information
    that allows identifying the resource-related API input
    arguments (i.e., input arguments that specify resources).
    With the adopted structure of the API configuration file,
    this input is a list of dictionaries, where each of them
    is dedicated to a specific input argument. Example:
    [{'TableName': 'None'}]. Note that both keys and values
    are expected to be strings. NOTE: if the API does not
    have any resource-related input arguments, None should
    be passed instead.
    -) api_call_ast_node: AST node of the API call.
    -) infrastruc_code_dict: Dictionary that maps the YAML
    file for the application under test.
    -) handler_name: Input specifying as a string the name
    of the relevant handler.
    -) sc_file: Source code file to be processed (full path).
    """
    # ================
    # Nested functions
    # ================
    def extract_permission_set(resource, permission_resource_dict, service):
        """
        Function that processes the permission-resource dictionary
        and returns the set of permissions for the specified resource
        and the specified cloud service.
        """
        return {perm_tuple[1] for perm_tuple in permission_resource_dict[resource]
                if perm_tuple[0] == service}
    # ================
    def get_close_match(resource_to_match, permission_resource_dict, service):
        """
        Function that processes the permission-resource dictionary
        and returns the key that best match the input resource_to_match.
        If no match is found, the function returns None.
        """
        for resource in permission_resource_dict:
            # Initialize object that allows handling the ARN
            resource_arn = AWSARNManagerCls(resource)
            # Check the service specified in the ARN
            if resource_arn.get_service() == service:
                # Check the ARN resource id
                if any([resource_arn.get_resource_id() == resource_to_match,
                        all([('/' in resource_arn.get_resource_id()),
                             resource_to_match in resource_arn.get_resource_id().split('/')])]):
                    return resource
    # ==================
    # Preliminary checks
    # ==================
    # Preliminary checks are implemented to identify specific cases
    # when the function can exit without running the main algorithm.
    if resources_info is None:
        print('--- No resource-related information for the API being processed ---')
        # It the API being processed does not have any resource-related
        # input argument, then the permissions are considered available.
        # This facilitates the integration with the analysis code that
        # extracts permissions-related information from other parts of
        # the YAML file.
        return True
    elif '*' in perm_res_dict:
        # If the wildcards syntax is used to specify permissions relevant
        # to the API being processed, then a detailed processing of the
        # resource-related API input arguments is not necessary. The
        # permissions for the relevant service specified with wildcards
        # syntax are compared with the permissions required for the API.
        print('--- Wildcards syntax detected - Performing checks... ---')
        permission_set = extract_permission_set('*', perm_res_dict, service_name)
        if permission_set & required_api_permissions != set():
            return True
    # ==============
    # Main algorithm
    # ==============
    print('--- Analysis of API resource-related input arguments is about to start... ---')
    # Auxiliary set initialization. The following cycle stores a
    # permission result for each resource-related input argument.
    permission_results = set()
    # Process all the resource-related API input arguments.
    for resource_dict in resources_info:
        # Retrieve resource-related input argument name and position
        resource_id, resource_pos_arg = list(resource_dict.items())[0]
        # ==================================
        # PART 1 - Process API call AST node
        # ==================================
        resource_input = get_call_input_ast_node(api_call_ast_node,
                                                 resource_id,
                                                 resource_pos_arg)
        if resource_input is None:
            # Since no information was extracted from the API call AST
            # node, the next step of the cycle can restart without any
            # further processing.
            continue
        # ======================================================
        # PART 2 - Process resource-related input argument value
        # ======================================================
        if isinstance(resource_input, ast.Constant) and isinstance(resource_input.value, str):
            # Find resource within permission-resource dictionary that
            # matches the string extracted by processing the AST node.
            resource_match = get_close_match(resource_input.value,
                                             perm_res_dict,
                                             service_name)
        else:
            # Attempt to resolve the resource input with dedicated function.
            resolved_resource_input = inspect_ast_node(resource_input,
                                                       infrastruc_code_dict,
                                                       handler_name,
                                                       sc_file)
            if resolved_resource_input is not None:
                # Find resource within permission-resource dictionary that
                # matches the string obtained by resolving the resource input.
                resource_match = get_close_match(resolved_resource_input,
                                                 perm_res_dict,
                                                 service_name)
            else:
                # The input argument does not hold a value that can be resolved,
                # and it cannot, therefore, be inspected with the adopted approach.
                # To simplify the integration with the analysis code that extracts
                # information about permissions from other parts of the YAML file,
                # permission is considered available. The next step of the cycle
                # can restart without any further processing.
                permission_results.add(True)
                continue
        # ===============================
        # PART 3 - Process resource match
        # ===============================
        if resource_match is not None:
            # A match for the resource specified as API input argument
            # has been found. The corresponding permissions in the
            # permission-resource dictionary are compared with those
            # required for the execution of the API.
            permission_set = extract_permission_set(resource_match,
                                                    perm_res_dict,
                                                    service_name)
            permission_results.add(permission_set & required_api_permissions != set())
        else:
            # APPROXIMATION: Since a resource match has not been found,
            # then the result depends on how accurately the resources
            # in the permission-resource dictionary have been resolved.
            # If all the resources have been fully resolved, and no
            # match was found, then it is reasonable to conclude that
            # the application does not have the permissions to execute
            # the API call.
            permission_results.add(not check_if_resolved(perm_res_dict))
    # The returned boolean flag takes into account the results
    # obtained for each resource-related API input argument.
    return all(permission_results)

# =======
# Classes
# =======
class PermissionsIdentifierCls:
    # === Constructor ===
    def __init__(self, config_dict):
        """
        Class constructor. It expects to receive a dictionary that maps
        the Serverless Framework YAML configuration file.
        """
        self.config_dict = config_dict
        # Data structures containing permission-related information
        # extracted by the methods implemented in this class.
        self.perm_dict = collections.defaultdict(set)
        self.perm_res_dict = collections.defaultdict(set)
        self.extract_perm_from_provider()
        self.extract_perm_for_resources()
        self.resolve_resources()

    # === Protected Method ===
    def _get_perm_dict_info(self):
        """
        Method extracting portion of the configuration dictionary with
        permissions-related information. Both modern and old Serverless
        Framework syntax supported.
        """
        # Init returned dictionary
        extr_perm_dict_info = {}
        try:
            try:
                extr_perm_dict_info = self.config_dict['provider']['iam']['role']['statements']
            except KeyError:
                extr_perm_dict_info = self.config_dict['provider']['iamRoleStatements']
        finally:
            return extr_perm_dict_info

    # === Method ===
    def extract_perm_for_resources(self):
        """
        Method extracting permissions-related information for resources
        explictly specified in the configuration dictionary.
        """
        try:
            extr_perm_dict_info = self._get_perm_dict_info()
            if isinstance(extr_perm_dict_info, list):
                # Extracted dictionaries are processed only if the key 'Resource' is found
                for extr_perm_dict in (elem for elem in extr_perm_dict_info if 'Resource' in elem):
                    if extr_perm_dict['Effect'] == 'Allow':
                        for perm in extr_perm_dict['Action']:
                            self.perm_res_dict[str(extr_perm_dict['Resource'])].update([(perm.split(':')[0].strip(), \
                                perm.split(':')[1].strip())])
                    else:
                        print('--- No information extracted - No allowed permission found ---')
            elif isinstance(extr_perm_dict_info, str):
                self.perm_res_dict['undefined'].add(extr_perm_dict_info)
            else:
                print('--- No information extracted - Unsupported data structure ---')
        except:
            print('--- Exception raised - No information extracted ---')

    # === Method ===
    def extract_perm_from_provider(self):
        """
        Method extracting permission-related information from provider tag.
        """
        try:
            extr_perm_dict_info = self._get_perm_dict_info()
            if isinstance(extr_perm_dict_info, list):
                for extr_perm_dict in extr_perm_dict_info:
                    if extr_perm_dict['Effect'] == 'Allow':
                        for perm in extr_perm_dict['Action']:
                            self.perm_dict[perm.split(':')[0].strip()].add(perm.split(':')[1].strip())
                    else:
                        print('--- No information extracted - No allowed permission found ---')
            elif isinstance(extr_perm_dict_info, str):
                self.perm_dict['undefined'].add(extr_perm_dict_info)
            else:
                print('--- No information extracted - Unsupported data structure ---')
        except:
            print('--- Exception raised - No information extracted ---')

    # === Method ===
    def get_num_of_services(self):
        return len(self.perm_dict)

    # === Method ===
    def pretty_print_perm_dict(self):
        for service in sorted(self.perm_dict):
            print_table([[perm] for perm in sorted(self.perm_dict[service])], \
                        ['Service ' + service])

    # === Method ===
    def pretty_print_resources(self):
        print_table([[resource] for resource in sorted(self.perm_res_dict)], \
                    ['Resources'])

    # === Method ===
    def resolve_resources(self):
        """
        Method that postprocesses the dictionary with permissions-related
        information for resources specified in the configuration dictionary
        to attempt to fully resolve the resources' ARNs.
        """
        # Initialize auxiliary dictionary
        temp_dict = {}
        for resource, permissions in self.perm_res_dict.items():
            # Store the permissions unaltered after attempting
            # to fully resolve the resource ARN.
            temp_dict[resolve_value_from_yaml(resource, self.config_dict)] = permissions
        # Update resource-permission dictionary
        self.perm_res_dict = temp_dict
