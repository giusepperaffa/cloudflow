# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast
import os

# =======
# Classes
# =======
class TypeAnnotationManagerCls:
    # === Constructor ===
    def __init__(self, repo_full_path):
        self.repo_full_path = repo_full_path
        # Interface module configuration dictionary
        self.interf_module_dict = {'name': 'boto3',
                                   'classes': ('client', 'resource')}

    # === Protected Method ===
    def _get_file_from_repo(self, extension='.py'):
        """
        Method that implements a generator yielding the
        full path of Python files within the repository
        being analysed.
        """
        for root, dirs, files in os.walk(self.repo_full_path):
            for flt_file in (file for file in files
                             if os.path.splitext(file)[1] == extension):
                yield os.path.join(root, flt_file)

    # === Protected Method ===
    def _get_filtered_file(self, mode):
        """
        Method that implements a generator yielding the
        full path of Python files within the repository.
        The code distinguishes the following cases:
        1) mode = 'full_import'. Only files where the
        interface module (boto3) is imported, i.e.,
        the statement 'import boto3' is included, are
        yielded.
        2) mode = 'partial_import'. Only files where at
        least one of the relevant classes of the interface
        module is imported, e.g., a statement such as 'from
        boto3 import client' is included, are yielded.
        NOTE: Import aliases are not processed and hence
        not supported.
        """
        if mode not in ('full_import', 'partial_import'):
            message = f'--- Unsupported input value in {self.__class__.__name__} ---'
            raise ValueError(message)
        # Initialize auxiliary variables
        module_name = self.interf_module_dict['name']
        class_names = self.interf_module_dict['classes']
        # Process files within the repository
        for file_full_path in self._get_file_from_repo():
            with open(file_full_path, mode='r') as file_obj:
                tree = ast.parse(file_obj.read())
                # Import statements are identified by traversing
                # the AST and checking the visited nodes' type.
                for node in ast.walk(tree):
                    # NOTE: The import aliases are never checked. These can be
                    # retrieved with the asname attribute (i.e., elem.asname).
                    # ------------------------------
                    # Case 1 - Module fully imported
                    # ------------------------------
                    if (mode == 'full_import') and (isinstance(node, ast.Import)):
                        if any(elem.name == module_name for elem in node.names):
                            yield file_full_path
                    # ---------------------------------------
                    # Case 2 - Only relevant classes imported
                    # ---------------------------------------
                    elif (mode == 'partial_import') and (isinstance(node, ast.ImportFrom)):
                        # The attribute level is different from zero in a relative
                        # import, which is specified in the source code with one or
                        # more dots (.). Relative imports are common in packages,
                        # but it would not make sense in this case, as the interface
                        # module is a third-party library. 
                        if all((node.module == module_name,
                                node.level == 0,
                                any(elem.name in class_names for elem in node.names))):
                            yield file_full_path

    # === Protected Method ===
    def _read_config_file(self):
        pass

    # === Method ===
    def add_type_annotations(self):
        """
        Method that adds the required type annotations to
        the interface objects, i.e., client and resource
        objects instantiated with the module that provides
        an interface to the cloud services.  
        """
        # Initialize auxiliary variables
        module_name = self.interf_module_dict['name']
        class_names = self.interf_module_dict['classes']
        # Process files within the repository
        for file_full_path in self._get_filtered_file('partial_import'):
            with open(file_full_path, mode='r') as file_obj:
                tree = ast.parse(file_obj.read())
                for node in ast.walk(tree):
                    # Assign statements are identified by traversing
                    # the AST and checking the visited nodes' type.
                    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                        # The value of the Assign node must be a Call node for
                        # the node to be relevant to the intended processing.
                        call_node = node.value
                        if all([call_node.func.value.id == module_name,
                                call_node.func.attr in class_names]):
                            # Typically, the first argument is specified with a
                            # string. If this is not the case, an exception is
                            # raised, and the information will not be extracted.
                            try:
                                print(call_node.args[0].value)
                            except AttributeError:
                                continue
                            print(call_node.lineno)
                        
    # === Method ===
    def add_imported_resources(self):
        pass
