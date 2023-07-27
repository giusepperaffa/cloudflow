# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast
import collections
import os
import re
import shutil

# =================
# Module Parameters
# =================
# List including the relevant Pysa source types
source_types = ['Test',
                'UserControlled']

# List including the relevant Pysa sink types
sink_types = ['Test']

# =======
# Classes
# =======
class HandlerModelGeneratorBaseCls:
    """
    Base class dedicated to the generation of  handler-related
    models. NOTE: this class should not be directly instantiated,
    as its functionality is designed to be used in derived classes.
    """
    # === Constructor ===
    def __init__(self, handlers_list, source_code, model_folder, \
                model_file='models.pysa'):
        """
        The constructor expects the following input arguments:
        -) handlers_list: List of strings specifying the handlers
        for which a model is required.
        -) source_code: Full path of the source code file where
        the handlers to be processed are stored.
        -) model_folder: Full path of the folder where the model
        file will be generated.
        -) model_file: Name of the model file. Default: models.pysa
        """
        self.handlers_list = handlers_list
        self.source_code = source_code
        self.model_folder = model_folder
        self.model_file = model_file
        # The model file full path (fp) is stored in an instance variable
        self.model_file_fp = os.path.join(self.model_folder, self.model_file)
        # List to be initialized with a child class
        self.ss_type_list = []

    # === Protected Method ===
    def _create_model(self, ast_node, source_sink_type):
        """
        Method that creates the model and returns it as a string.
        """
        module_name = os.path.splitext(os.path.basename(self.source_code))[0]
        func_name = ast_node.name
        # Fully qualified names are needed by Pysa
        qual_name = module_name + '.' + func_name
        # The first input argument of the processed function is processed
        # to add Pysa-specific information
        func_input = ast_node.args.args[0].arg
        func_input += ': ' + self._get_analysis_tool_annotation(source_sink_type)
        func_input = '(' + func_input + '):'
        return ' '.join(['def', qual_name + func_input, str('...')])

    # === Protected Method ===
    def _get_file_mode(self):
        """
        Method that returns the file mode (append or write) to be used
        to generate the model file. The append mode prevents an existing
        file from being overwritten.
        """
        if os.path.isfile(self.model_file_fp):
            return 'a'
        else:
            return 'w'

    # === Protected Method ===
    def _get_analysis_tool_annotation(self, source_sink_type):
        """
        Method that obtains the annotation-like information
        necessary for the model. NOTE: the code extracts this
        information by processing the class name.
        """
        # Regular expression used to process the class name (cn)
        cn_proc_reg_exp = re.compile(r'([A-Z][a-z]+)')
        cn_proc = cn_proc_reg_exp.findall(self.__class__.__name__)[1]
        return 'Taint' + cn_proc + '[' + source_sink_type + ']'

    # === Public Method ===
    def generate_models(self):
        """
        Method that generates the required models.
        """
        # Consistency check
        if self.ss_type_list == []:
            raise NotImplementedError('--- Inconsistency detected - Missing initialization ---')
        print(f'--- Pysa model is being generated with class {self.__class__.__name__}... ---')
        with open(self.model_file_fp, mode=self._get_file_mode()) as m_file,\
            open(self.source_code, mode='r') as sc_file:
            # Add comment to model file (readability)
            m_file.write('# Handler-related models' + '\n')
            # Obtain Abstract Syntax Tree (AST) for source code
            tree = ast.parse(sc_file.read())
            # Processing of all the function definition nodes
            for func_node in (node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)):
                # Functions for which no model is required are filtered out
                if func_node.name in self.handlers_list:
                    for ss_type in self.ss_type_list:
                        m_file.write(self._create_model(func_node, ss_type) + '\n')
            else:
                # Add newline character to model file (readability)
                m_file.write('\n')

class HandlerSourceModelGeneratorCls(HandlerModelGeneratorBaseCls):
    """
    Class dedicated to the generation of source-specific handler-related models.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Completion of the initialization provided in the base class
        self.ss_type_list = source_types

class HandlerSinkModelGeneratorCls(HandlerModelGeneratorBaseCls):
    """
    Class dedicated to the generation of sink-specific handler-related models.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Completion of the initialization provided in the base class
        self.ss_type_list = sink_types

class ModelGenerationManagerCls:
    """
    Class that provides an interface to the classes that
    generate Pysa models. Data structures initialized by
    the module analysisreslib are used to instantiate an
    object of this class. Furthermore, this class copies
    all the generic Pysa models available within the
    tool repository in the analysis folder.
    """
    # === Constructor ===
    def __init__(self,
                 handlers_dict,
                 infrastruc_code_dict,
                 infrastruc_code_file,
                 model_folder):
        """
        Class constructor. Input arguments:
        -) handlers_dict: Data structure initialized within
        the module analysisreslib.
        -) infrastruc_code_dict: Data structure initialized
        within the module analysisreslib.
        -) infrastruc_code_file: Full path of the YAML file.
        -) model_folder: String containing the full path of
        the folder where the Pysa models have to be stored.
        """
        # Attribute initialization
        self.handlers_dict = handlers_dict
        self.infrastruc_code_dict = infrastruc_code_dict
        self.infrastruc_code_file = infrastruc_code_file
        self.model_folder = model_folder
        # Auxiliary methods execution
        self.init_model_gen_cls_list()
        self.init_sc_to_handlers_dict()
        self.copy_generic_models()

    # === Method ===
    def copy_generic_models(self, generic_models_folder='pysamodels'):
        """
        Method that copies all the generic Pysa models
        available within the tool repository in the
        analysis folder (sub-folder dedicated to the
        Pysa models).
        """
        # Full path of the folder containing the generic Pysa models
        gm_folder_full_path = os.path.join(os.sep.join(__file__.split(os.sep)[:-2]), generic_models_folder)
        # Only the files with the Pysa models extension are copied
        for flt_file in (elem for elem in os.listdir(gm_folder_full_path)
                         if os.path.splitext(elem)[1] == '.pysa'):
            shutil.copy2(os.path.join(gm_folder_full_path, flt_file), self.model_folder)

    # === Method ===
    def generate_models(self):
        """
        Method that generates all the Pysa models by
        relying on dedicated classes.
        """
        for model_gen_cls in self.model_gen_cls_list:
            # The following cycle is necessary because model generation
            # classes have been designed to process only one source code
            # file at a time.
            for sc_file, handlers_list in self.sc_to_handlers_dict.items():
                try:
                    # Instantiation of model generator object
                    model_generator = model_gen_cls(handlers_list,
                                                    sc_file,
                                                    self.model_folder)
                    # Generation of Pysa models with dedicated method
                    model_generator.generate_models()
                except Exception as e:
                    print('--- Exception raised while generating Pysa models with class: ---')
                    print(f'--- {model_gen_cls} ---')
                    print('--- Exception details: ---')
                    print(f'--- {e} ---')

    # === Method ===
    def init_model_gen_cls_list(self):
        """
        Method that initializes a list of classes that
        will be used to generate the Pysa models. Such
        classes generate different types of models.
        NOTE: When new classes are available, the list
        needs to be updated.
        """
        self.model_gen_cls_list = [HandlerSourceModelGeneratorCls,
                                   HandlerSinkModelGeneratorCls]

    # === Method ===
    def init_sc_to_handlers_dict(self):
        """
        Method that initializes a dictionary that maps
        the following keys and values:
        -) Keys: Strings with full path of the source
        code files containing handlers for which Pysa
        models have to be generated.
        -) Values: List of strings with handlers names
        (i.e., function names) for which Pysa models
        have to be generated.
        """
        # Dictionary initialization
        self.sc_to_handlers_dict = collections.defaultdict(list)
        # The processing implemented in this method takes
        # into account that the lambda handlers within
        # the YAML file are specified by including:
        # 1) A path relative to the YAML file
        # 2) The name of the Python module
        infrastruc_code_file_folder = os.path.dirname(self.infrastruc_code_file)
        for handler_name in self.handlers_dict:
            # Remove './' in front of information extracted
            # from YAML file to facilitate path joining step
            handler_path_info = self.infrastruc_code_dict['functions'][handler_name]['handler']
            handler_path_info = re.sub(r'^\./', '', handler_path_info)
            # Separate handler function name from the extracted path
            handler_rel_path, handler_func = handler_path_info.split('.')
            # Store extracted information
            self.sc_to_handlers_dict[os.path.join(infrastruc_code_file_folder,
                                                  handler_rel_path + '.py')].append(handler_func)
