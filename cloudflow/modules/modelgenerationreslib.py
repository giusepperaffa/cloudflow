# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast
import os
import re

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
        print(f'--- Model generation with {self.__class__.__name__} - Start ---')
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
