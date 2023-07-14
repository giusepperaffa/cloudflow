# ========================================
# Import Python Modules (Standard Library)
# ========================================
import collections

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.utils.customprintreslib import print_table

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
    def pretty_print_perm_dict(self):
        for service in sorted(self.perm_dict):
            print_table([[perm] for perm in sorted(self.perm_dict[service])], \
                        ['Service ' + service])

    # === Method ===
    def pretty_print_resources(self):
        print_table([[resource] for resource in sorted(self.perm_res_dict)], \
                    ['Resources'])
