# ========================================
# Import Python Modules (Standard Library)
# ========================================
import collections
import yaml
import sys

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
        # Data structure containing permission-related information
        # extracted by the methods implemented in this class.
        self.perm_dict = collections.defaultdict(set)
        self.extract_perm_from_provider()

    # === Method ===
    def extract_perm_from_provider(self):
        """
        Method extracting permission-related information from provider
        entry. Both modern and old Serverless Framework syntax supported.
        """
        try:
            try:
                extr_perm_dict_info = self.config_dict['provider']['iam']['role']['statements']
            except KeyError:
                extr_perm_dict_info = self.config_dict['provider']['iamRoleStatements']
            finally:
                if isinstance(extr_perm_dict_info, list):
                    for extr_perm_dict in extr_perm_dict_info:
                        if extr_perm_dict['Effect'] == 'Allow':
                            for perm in extr_perm_dict['Action']:
                                self.perm_dict[perm.split(':')[0].strip()].add(perm.split(':')[1].strip())
                        else:
                            print("--- Inconsistency detected - 'Effect' entry not found ---")
                elif isinstance(extr_perm_dict_info, str):
                    self.perm_dict['undefined'].add(extr_perm_dict_info)
                else:
                    print('--- No information extracted - Unsupported data structure ---')
        except:
            print('--- Exception raised - No information extracted ---')

    # === Method ===
    def pretty_print_perm_dict(self):
        for service in sorted(self.perm_dict):
            header_str = f'*** Service: {service} ***'
            print()
            print(len(header_str) * '*')
            print(header_str)
            print(len(header_str) * '*')
            for perm in sorted(self.perm_dict[service]):
                print(f'--- {perm} ---')
