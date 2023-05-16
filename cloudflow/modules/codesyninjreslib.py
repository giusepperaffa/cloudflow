# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast
import astor
import collections
import os
import yaml
from typing import NamedTuple

# =======
# Classes
# =======
class InterfaceRecordCls(NamedTuple):
    line_no: int
    instance_name: str
    instance_type: str
    service: str

class TypeAnnotationManagerCls:
    """
    Class providing the functionality that allows adding the
    required type annotations to the processed files as well
    as the special modules needed for these type annotations
    to be correctly used by the static analysis tool.
    """
    # === Constructor ===
    def __init__(self, repo_full_path):
        """
        Class constructor. The repository full path has
        has to be passed as string.
        """
        self.repo_full_path = repo_full_path
        # The data structures and the processing implemented in this
        # class distinguish between fully imported (i.e., import boto3)
        # and partially imported (e.g., from boto3 import client)
        # interface module.
        self.import_modes = ('partial', 'full')
        # Interface module configuration dictionary
        self.interf_module_dict = {'name': 'boto3',
                                   'classes': ('client', 'resource')}
        # Information about the interface objects extracted by this
        # class is stored in a nested dictionary that facilitates the
        # implementation of some of its methods and that can be used
        # outside this class. The nested keys are strings storing
        # full paths of repository files.
        self.interf_objs_dict = {import_mode: collections.defaultdict(list) for
                                 import_mode in self.import_modes}

    # === Protected Method ===
    def _add_imported_resources(self, import_mode):
        """
        Method that adds the commands necessary to import
        the required resources from the stub modules. The
        values supported for import_mode are stored in the
        instance variable import_modes.
        """
        # Process source code file
        for sc_file in (file_full_path for file_full_path in self._get_filtered_file(import_mode)
                        if file_full_path in self.interf_objs_dict[import_mode]):
            # Adds type annotations within in-memory data structure
            with open(sc_file, mode='r') as sc_file_obj:
                tree = ast.parse(sc_file_obj.read())
                # Processing of the list of interface objects' records
                for interf_record in self.interf_objs_dict[import_mode][sc_file]:
                    # Name of the module containing the relevant stubs
                    stub_module = self.config_dict[interf_record.service]['stub_module']
                    # Annotation to be included in the new import statement
                    type_ann = self.config_dict[interf_record.service][interf_record.instance_type + '_obj']
                    # Create AST node with import statement
                    import_statement = ast.ImportFrom(module=stub_module,
                                                      names=[ast.alias(name=type_ann, asname=None)],
                                                      level=0)
                    # Add the new import statement as first line of processed file
                    tree.body.insert(0, import_statement)
                    # Add lineno & col_offset to the created node
                    ast.fix_missing_locations(import_statement)
            # Overwrite source code file to include modifications
            with open(sc_file, mode='w') as sc_file_obj:
                sc_file_obj.write(astor.to_source(tree))

    # === Protected Method ===
    def _add_type_annotations(self, import_mode):
        """
        Method that adds the required type annotations to
        the interface objects, i.e., client and resource
        objects instantiated with the module that provides
        an interface to the cloud services. The values
        supported for import_mode are stored in the instance
        variable import_modes.
        """
        # Process source code file
        for sc_file in (file_full_path for file_full_path in self._get_filtered_file(import_mode)
                        if file_full_path in self.interf_objs_dict[import_mode]):
            # Adds type annotations within in-memory data structure
            with open(sc_file, mode='r') as sc_file_obj:
                tree = ast.parse(sc_file_obj.read())
                tree = TypeAnnotationTransformerCls(self.interf_objs_dict[import_mode][sc_file],
                                                    self._read_config_file()).visit(tree)
            # Overwrite source code file to include annotations
            with open(sc_file, mode='w') as sc_file_obj:
                sc_file_obj.write(astor.to_source(tree)) 

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
    def _get_filtered_file(self, import_mode):
        """
        Method that implements a generator yielding the
        full path of Python files within the repository.
        The code distinguishes the following cases:
        1) import_mode = 'full'. Only files where the
        interface module (boto3) is imported, i.e.,
        the statement 'import boto3' is included, are
        yielded.
        2) import_mode = 'partial'. Only files where at
        least one of the relevant classes of the interface
        module is imported, e.g., a statement such as 'from
        boto3 import client' is included, are yielded.
        NOTE: Import aliases are not processed and hence
        not supported.
        """
        # Consistency check
        if import_mode not in self.import_modes:
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
                    if (import_mode == 'full') and (isinstance(node, ast.Import)):
                        if any(elem.name == module_name for elem in node.names):
                            yield file_full_path
                    # ---------------------------------------
                    # Case 2 - Only relevant classes imported
                    # ---------------------------------------
                    elif (import_mode == 'partial') and (isinstance(node, ast.ImportFrom)):
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
    def _get_interf_obj_instance_type(self, import_mode, call_node):
        """
        Method that inspects the passed ast Call node to
        return the interface instance type, i.e., client
        or resource in the case of the boto3 library. The
        values supported for import_mode are stored in the
        instance variable import_modes.
        """
        if import_mode == 'full':
            return call_node.func.attr
        elif import_mode == 'partial':
            return call_node.func.id

    # === Protected Method ===
    def _identify_interf_obj_node(self, import_mode, call_node):
        """
        Method that inspects the passed ast Call node to
        identify interface objects, i.e., boto3 client or
        resource objects. The method always returns a Boolean,
        but the implemented checks depend on the import_mode
        input variable. The values supported for import_mode
        are stored in the instance variable import_modes.
        """
        # Initialize auxiliary variables
        module_name = self.interf_module_dict['name']
        class_names = self.interf_module_dict['classes']
        # AST node processing
        if import_mode == 'full':
            return all([call_node.func.value.id == module_name,
                        call_node.func.attr in class_names])
        elif import_mode == 'partial':
            return call_node.func.id in class_names

    # === Method ===
    def _init_interf_objs_dict(self, import_mode):
        """
        Method that initializes and stores in an instance variable
        the dictionary with information about the interface objects.
        NOTE: This method must be called before adding the type
        annotations to the source code.
        """
        # Process files within the repository
        for file_full_path in self._get_filtered_file(import_mode):
            with open(file_full_path, mode='r') as file_obj:
                tree = ast.parse(file_obj.read())
                for node in ast.walk(tree):
                    # Assign statements are identified by traversing
                    # the AST and checking the visited nodes' type.
                    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                        # The value of the Assign node must be a Call node for
                        # the node to be relevant to the intended processing.
                        call_node = node.value
                        if self._identify_interf_obj_node(import_mode, call_node):
                            # Typically, the first argument is specified with a
                            # string. If this is not the case, an exception is
                            # raised, and the information will not be extracted.
                            try:
                                # Initialize interface record object
                                interf_record = InterfaceRecordCls(call_node.lineno,
                                                                   node.targets[0].id,
                                                                   self._get_interf_obj_instance_type(import_mode,
                                                                                                      call_node),
                                                                   call_node.args[0].value)
                                # Update interface object dictionary
                                self.interf_objs_dict[import_mode][file_full_path].append(interf_record)
                            except AttributeError:
                                continue

    # === Protected Method ===
    def _read_config_file(self,
                          config_folder='config',
                          config_file='type_annotation_config_file.yml'):
        """
        Method that maps the configuration file dedicated to type
        annotations into a dictionary, which is stored in an instance
        variable and returned.
        """
        # Full path of the folder containing the configuration file
        config_folder_full_path = os.path.join(os.sep.join(__file__.split(os.sep)[:-2]), config_folder)
        # The configuration file is mapped into a dictionary and returned
        with open(os.path.join(config_folder_full_path, config_file), mode='r') as config_file_obj:
            self.config_dict = yaml.load(config_file_obj, Loader=yaml.BaseLoader)
        return self.config_dict

    # === Method ===
    def add_all_type_annotations(self):
        """
        Method that adds all the necessary type annotations
        and all the import statements that these require.   
        """
        for import_mode in self.import_modes:
            self._init_interf_objs_dict(import_mode)
            self._add_type_annotations(import_mode)
            self._add_imported_resources(import_mode)

class TypeAnnotationTransformerCls(ast.NodeTransformer):
    """
    Class providing the functionality required to type-annotate
    selected AST nodes. 
    """
    # === Constructor ===
    def __init__(self, interf_objs_records_list, config_dict):
        """
        Class constructor. The input arguments are data structures
        initialized by the class TypeAnnotationManagerCls.
        """
        super().__init__()
        self.interf_objs_records_list = interf_objs_records_list
        self.config_dict = config_dict

    # === Method ===
    def visit_Assign(self, node):
        try:
            # Filter relevant interface object record
            flt_interf_record = [interf_record for interf_record in self.interf_objs_records_list
                                 if node.value.lineno == interf_record.line_no][0]
            # Identify relevant type annotation
            type_ann = self.config_dict[flt_interf_record.service][flt_interf_record.instance_type + '_obj']
            # Create annotated AST node
            annotated_node = ast.AnnAssign(target=node.targets[0],
                                           annotation=ast.Name(id=type_ann, ctx=ast.Load()),
                                           value=node.value,
                                           simple=True)
            # Add lineno & col_offset to the node created programmatically
            ast.copy_location(annotated_node, node)
            ast.fix_missing_locations(annotated_node)
            return annotated_node
        except:
            return node
