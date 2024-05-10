# ========================================
# Import Python Modules (Standard Library)
# ========================================
import collections

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.utils.customprintreslib import print_table
from cloudflow.modules.customresolverreslib import resolve_value_from_yaml

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
