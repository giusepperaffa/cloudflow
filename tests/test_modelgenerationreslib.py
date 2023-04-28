# =========================================
# Import Python Modules (Stanadard Library)
# =========================================
import os
import pytest
import re
import sys

# ================
# Script Variables
# ================
repo_full_path = os.sep.join(os.path.realpath(__file__).split(os.sep)[:-2])

# ========================================
# Import Python Modules (Project-specific)
# ========================================
from cloudflow.modules.modelgenerationreslib import HandlerSourceModelGeneratorCls, \
    HandlerSinkModelGeneratorCls

# ========
# Fixtures
# ========
@pytest.fixture
def get_test_files_folder():
    return os.path.join(repo_full_path, 'tests', \
        'test-files', os.path.splitext(__file__.split('_')[1])[0])

@pytest.fixture
def reg_exp_new_line():
    return re.compile(r'\n$')

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

# ==============
# Test Functions
# ==============
def test_handler_source_model_only(get_test_files_folder,
                                   reg_exp_new_line,
                                   model_file_delete):
    test_file = os.path.join(get_test_files_folder, 'handlers.py')
    # Create instance of class that generates model file
    hsm_obj = HandlerSourceModelGeneratorCls(['lambda_handler_1', 'lambda_handler_2'],
                                             test_file,
                                             get_test_files_folder)
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
                                   model_file_delete):
    test_file = os.path.join(get_test_files_folder, 'handlers.py')
    # Create instance of class that generates model file
    hsm_obj = HandlerSinkModelGeneratorCls(['lambda_handler_1', 'lambda_handler_2'],
                                             test_file,
                                             get_test_files_folder)
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
                                   model_file_delete):
    test_file = os.path.join(get_test_files_folder, 'handlers.py')
    # Create instances of classes that generate model file
    h_source_model_obj = HandlerSourceModelGeneratorCls(['lambda_handler_1', 'lambda_handler_2'],
                                             test_file,
                                             get_test_files_folder)
    h_sink_model_obj = HandlerSinkModelGeneratorCls(['lambda_handler_1', 'lambda_handler_2'],
                                             test_file,
                                             get_test_files_folder)
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
