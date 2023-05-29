# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast
import astor
import os
import yaml

# =======
# Classes
# =======
class CodeSynInjManagerCls:
    """
    Class that provides the functionality to add synthesized
    handler calls to the analysed repository to simulate a
    synchronous-like execution flow. The class relies on data
    structures provided by other modules of the tool. 
    """
    # === Constructor ===
    def __init__(self,
                 interf_objs_dict,
                 perm_dict,
                 handlers_dict):
        """
        Class constructor.
        """
        # Data structure with information about interface objects 
        self.interf_objs_dict = interf_objs_dict
        # Data structure containing permissions-related information
        self.perm_dict = perm_dict
        # Data structure containing handlers-related information
        self.handlers_dict = handlers_dict

    # === Protected Method ===
    def _get_source_code_info(self):
        """
        Method that implements a generator processing information
        extracted from the data structure dedicated to the
        interface objects. A tuple with the following elements
        is yielded:
        1) Full path of source code file.
        2) Data structure with information on interface objects
        in source code file.
        """
        for import_mode in self.interf_objs_dict:
            for sc_file in self.interf_objs_dict[import_mode]:
                yield sc_file, self.interf_objs_dict[import_mode][sc_file]

    # === Protected Method ===
    def _read_config_file(self,
                          config_folder='config',
                          config_file='api_info_config_file.yml'):
        """
        Method that maps the configuration file dedicated to the
        interface module API information into a dictionary, which
        is stored in an instance variable and returned. 
        """
        # Full path of the folder containing the configuration file
        config_folder_full_path = os.path.join(os.sep.join(__file__.split(os.sep)[:-2]), config_folder)
        # The configuration file is mapped into a dictionary and returned
        with open(os.path.join(config_folder_full_path, config_file), mode='r') as config_file_obj:
            self.config_dict = yaml.load(config_file_obj, Loader=yaml.BaseLoader)
        return self.config_dict

    # === Method ===
    def inject_synthesized_code(self):
        """
        Method that injects synthesized code to simulate a
        synchronous-like execution flow.
        """
        print('--- Synthesized handler calls are about to be injected ---')
        for sc_file, interf_objs_info_list in self._get_source_code_info():
            print('--- The following file is about to be processed: ---')
            print(f'--- {sc_file} ---')
            for interf_record in interf_objs_info_list:
                # Adds synthesized code within in-memory data structure
                with open(sc_file, mode='r') as sc_file_obj:
                    tree = ast.parse(sc_file_obj.read())
                    # Create instance of class that modifies the source code
                    walker = CodeSynthesisInjectionCls(interf_record,
                                                       self.perm_dict,
                                                       self.handlers_dict,
                                                       self._read_config_file())
                    walker.walk(tree)
                # Overwrite source code file to include synthesized code
                with open(sc_file, mode='w') as sc_file_obj:
                    sc_file_obj.write(astor.to_source(tree))

class CodeSynthesisInjectionCls(astor.TreeWalk):
    """
    Class that customizes the tree traversal implemented by
    the base class astor.TreeWalk to inject a function call
    after another function call. This code was implemented
    using the example available in question 41764207 on Stack
    Overflow as baseline.
    """
    # === Constructor ===
    def __init__(self,
                 interf_record,
                 perm_dict,
                 handlers_dict,
                 config_dict):
        super().__init__()
        self.interf_record = interf_record
        self.perm_dict = perm_dict
        self.handlers_dict = handlers_dict
        self.config_dict = config_dict

    # === Protected Method ===
    def _check_api_permissions(self,
                              service,
                              interf_obj_type,
                              api_name):
        """
        Method that checks whether the permissions required for
        the execution of the specified API are present in the
        repository infrastructure code file. If so, the API can
        be executed and True is returned, False otherwise.
        NOTE: This method must be run only on APIs specified in
        the tool config file, otherwise an unhandled exception
        is raised.
        """
        # Required permissions for the API are extracted from configuration dictionary  
        required_permissions = set(self.config_dict[service][interf_obj_type + '_obj'][api_name]['permissions'])
        # If the intersection between the required permissions and those specified
        # in the repository infrastructure code YAML file is a non-empty set, then
        # the execution of the API is allowed.    
        return (required_permissions & self.perm_dict[service]) != set([])

    # === Protected Method ===
    def _check_api_support(self,
                           service,
                           interf_obj_type,
                           api_name):
        """
        Method that checks whether the specified API for a given
        service and a given interface object type (i.e., client
        or resouce) is present in the configuration file. If so,
        True is returned, False otherwise.
        """
        try:
            if api_name in self.config_dict[service][interf_obj_type + '_obj']:
                return True
            else:
                print(f'--- API {api_name} not specified in the configuration file ---')
                return False
        except KeyError as e:
            print(f'--- API {api_name} could not be checked in the configuration file ---')
            print(f'--- The following tag is missing in the configuration file: ---')
            print(f'--- {e} ---')
            return False

    # === Method ===
    def pre_body_name(self):
        pass

    # === Method ===
    def pre_Call(self):
        """
        Method that processes instances of the class Call (module ast).
        Such instances have a func attribute, which normally is a Name
        or an Attribute object. Since the purpose of the class is to
        inject code after API calls on an interface object, the code
        assumes that the func attribute is an Attribute object. For  
        further information on the Call class of the Standard Library
        module ast, refer to:
        https://greentreesnakes.readthedocs.io/en/latest/nodes.html#Call
        """
        # The purpose of this method is to initialize the private
        # attribute __name. When the initialization is not possible
        # or fails, the default value will remain unchanged.
        self.__name = None
        try:
            # Check interface object instance name and if API call is supported
            if all([self.interf_record.instance_name == self.cur_node.func.value.id,
                    self._check_api_support(self.interf_record.service,
                                            self.interf_record.instance_type,
                                            self.cur_node.func.attr)]):
                # Check permissions required to execute the API call
                print(f'--- Permissions for API {self.cur_node.func.attr} being checked... ---')
                if self._check_api_permissions(self.interf_record.service,
                                               self.interf_record.instance_type,
                                               self.cur_node.func.attr):
                    print('--- Code synthesis and injection only partially implemented ---')
        except AttributeError:
            # This exception is raised every time the func attibute of
            # the of Call object is not an Attribute object. To avoid
            # noisy log files, no message is printed in this case.
            pass 
        except Exception as e:
            print('--- Exception raised during code synthesis and injection - Details: ---')
            print(f'--- {e} ---')
        return True
