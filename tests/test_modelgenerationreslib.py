# =========================================
# Import Python Modules (Stanadard Library)
# =========================================
import os
import pytest
import re

# ========================================
# Import Python Modules (Project-specific)
# ========================================
from cloudflow.modules.modelgenerationreslib import HandlerSourceModelGeneratorCls, \
    HandlerSinkModelGeneratorCls
from cloudflow.modules.toolconfigreslib import ToolConfigManagerCls

# =======
# Classes
# =======
class MockFoldersManagerCls:
    """
    Class the mocks the tool's folders manager class.
    The purpose is to expose only the attributes required
    by the tests included in this module.
    """
    def __init__(self, pysa_models_folder, repo_full_path):
        """
        Class constructor. Input arguments:
        -) pysa_models_folder: String specifying the full
        path of the folder containing the Pysa models.
        -) repo_full_path: String specifying the full path
        of the folder containing the repository analysed
        by the tool.
        """
        self.pysa_models_folder = pysa_models_folder
        self.repo_full_path = repo_full_path

# ========
# Fixtures
# ========
@pytest.fixture
def get_mock_folders_manager(get_test_files_folder):
    """
    Fixture that returns an instance of class that mocks the
    folders manager. The same folder can be used to initialize
    both input arguments of the class constructor, because the
    attribute dedicated to the analysed repository full path
    does not have a match in the tool configuration file (the
    latter is set to None).
    """
    return MockFoldersManagerCls(get_test_files_folder, get_test_files_folder)

@pytest.fixture
def get_test_files_folder(get_main_test_files_folder):
    return os.path.join(get_main_test_files_folder,
                        os.path.splitext(os.path.basename(__file__))[0].split('_')[1])

@pytest.fixture
def get_tool_config_manager():
    """
    Fixture that returns an instance of the tool configuration
    manager class. The constructor input argument of the latter
    is set up to None because the implementation of the tests
    within this module does not rely on any tool configuration
    file.
    """
    return ToolConfigManagerCls(None)

@pytest.fixture
def model_file_delete(get_test_files_folder):
    """
    Fixture that deletes generated model files. It contains
    yield instead of return, and it is executed after the
    test function. More details on this mechanism at:
    https://docs.pytest.org/en/6.2.x/fixture.html#yield-fixtures-recommended
    """  
    yield
    for elem in os.listdir(get_test_files_folder):
        if os.path.splitext(elem)[1] == '.pysa':
            os.remove(os.path.join(get_test_files_folder, elem))

@pytest.fixture
def reg_exp_new_line():
    return re.compile(r'\n$')

# ==============
# Test Functions
# ==============
def test_handler_source_model_only(get_test_files_folder,
                                   reg_exp_new_line,
                                   model_file_delete,
                                   get_tool_config_manager,
                                   get_mock_folders_manager):
    test_file = os.path.join(get_test_files_folder, 'handlers.py')
    # Create instance of class that generates model file
    hsm_obj = HandlerSourceModelGeneratorCls(['lambda_handler_1', 'lambda_handler_2'],
                                             test_file,
                                             get_mock_folders_manager,
                                             get_tool_config_manager)
    hsm_obj.generate_models()
    # Expected lines in the generated model file
    expected_lines = ['def handlers.lambda_handler_1(event: TaintSource[Test]): ...',
                      'def handlers.lambda_handler_1(event: TaintSource[UserControlled]): ...',
                      'def handlers.lambda_handler_2(event: TaintSource[Test]): ...',
                      'def handlers.lambda_handler_2(event: TaintSource[UserControlled]): ...']
    # Check generated model file
    gen_model_file = os.path.join(get_test_files_folder, 'models.pysa')
    with open(gen_model_file, mode='r') as gen_model_file_obj:
        # Initialize a set containing the lines of the generated model file
        # Lines are processed with a regular expression
        gen_model_file_lines = set(reg_exp_new_line.sub('', line) for line
                                   in gen_model_file_obj.readlines())
        for expected_line in expected_lines:
            assert expected_line in gen_model_file_lines

def test_handler_sink_model_only(get_test_files_folder,
                                   reg_exp_new_line,
                                   model_file_delete,
                                   get_tool_config_manager,
                                   get_mock_folders_manager):
    test_file = os.path.join(get_test_files_folder, 'handlers.py')
    # Create instance of class that generates model file
    hsm_obj = HandlerSinkModelGeneratorCls(['lambda_handler_1', 'lambda_handler_2'],
                                             test_file,
                                             get_mock_folders_manager,
                                             get_tool_config_manager)
    hsm_obj.generate_models()
    # Expected lines in the generated model file
    expected_lines = ['def handlers.lambda_handler_1(event: TaintSink[Test]): ...',
                      'def handlers.lambda_handler_2(event: TaintSink[Test]): ...',]
    # Check generated model file
    gen_model_file = os.path.join(get_test_files_folder, 'models.pysa')
    with open(gen_model_file, mode='r') as gen_model_file_obj:
        # Initialize a set containing the lines of the generated model file
        # Lines are processed with a regular expression
        gen_model_file_lines = set(reg_exp_new_line.sub('', line) for line
                                   in gen_model_file_obj.readlines())
        for expected_line in expected_lines:
            assert expected_line in gen_model_file_lines

def test_handler_source_and_sink_models(get_test_files_folder,
                                   reg_exp_new_line,
                                   model_file_delete,
                                   get_tool_config_manager,
                                   get_mock_folders_manager):
    test_file = os.path.join(get_test_files_folder, 'handlers.py')
    # Create instances of classes that generate model file
    h_source_model_obj = HandlerSourceModelGeneratorCls(['lambda_handler_1', 'lambda_handler_2'],
                                             test_file,
                                             get_mock_folders_manager,
                                             get_tool_config_manager)
    h_sink_model_obj = HandlerSinkModelGeneratorCls(['lambda_handler_1', 'lambda_handler_2'],
                                             test_file,
                                             get_mock_folders_manager,
                                             get_tool_config_manager)
    h_source_model_obj.generate_models()
    h_sink_model_obj.generate_models()
    # Expected lines in the generated model file
    expected_lines = ['def handlers.lambda_handler_1(event: TaintSource[Test]): ...',
                      'def handlers.lambda_handler_1(event: TaintSink[Test]): ...']
    # Check generated model file
    gen_model_file = os.path.join(get_test_files_folder, 'models.pysa')
    with open(gen_model_file, mode='r') as gen_model_file_obj:
        # Initialize a set containing the lines of the generated model file
        # Lines are processed with a regular expression
        gen_model_file_lines = set(reg_exp_new_line.sub('', line) for line
                                   in gen_model_file_obj.readlines())
        for expected_line in expected_lines:
            assert expected_line in gen_model_file_lines
