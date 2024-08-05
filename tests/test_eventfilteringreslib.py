# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast
import os
import pytest

# ========================================
# Import Python Modules (Project-specific)
# ========================================
from cloudflow.utils.fileprocessingreslib import extract_dict_from_yaml
from cloudflow.modules.eventfilteringreslib import EventFilteringManagerCls, analyse_event_filtering

# ===================
# Auxiliary Functions
# ===================
def extract_api_call_ast_node(source_code_full_path,
                              call_func_id='s3_client',
                              call_attr_value='upload_file'):
    """
    Function that extracts and returns the AST node
    of an API call (ast.Call type) from the source
    code file specified as input parameter (string).
    If the AST Call node does not meet the conditions
    specified by the optional input parameters, None
    is returned.
    """
    with open(source_code_full_path) as sc_file_obj:
        # Obtain in-memory data structure
        tree = ast.parse(sc_file_obj.read())
        # Identify all AST Call nodes
        for flt_node in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
            try:
                # Identify AST Call nodes that meet specific conditions
                if all([flt_node.func.value.id == call_func_id,
                        flt_node.func.attr == call_attr_value]):
                    return flt_node
            except:
                pass
    return

# ========
# Fixtures
# ========
@pytest.fixture
def get_test_files_folder(get_main_test_files_folder):
    return os.path.join(get_main_test_files_folder,
                        os.path.splitext(os.path.basename(__file__))[0].split('_')[1])

# ==============
# Test Functions
# ==============
@pytest.mark.parametrize('handler, input_to_check, expected_result', [
    ('onS3Upload', 'uploads/my-file.txt', True),
    ('onS3Upload', 'upload-folder/my-file.txt', False),
    ('onS3Upload', 'uploads/my-file.jpg', False),
])
def test_string_literal(get_test_files_folder, handler, input_to_check, expected_result):
    infrastruc_code_dict = extract_dict_from_yaml(get_test_files_folder, 'serverless_s3_event_filtering.yml')
    event_filtering_manager = EventFilteringManagerCls(infrastruc_code_dict,
                                                       's3',
                                                       handler,
                                                       None)
    result = event_filtering_manager.get_event_filtering_result(input_to_check, 'resolved')
    assert result == expected_result

@pytest.mark.parametrize('handler, var, expected_result', [
    ('onS3Upload', 's3_bucket_key_1', True),
    ('onS3Upload', 's3_bucket_key_2', False),
    ('onS3Upload', 's3_bucket_key_3', True),
    ('onS3Upload', 'non_existent_var', True),
])
def test_source_code_var(get_test_files_folder, handler, var, expected_result):
    infrastruc_code_dict = extract_dict_from_yaml(get_test_files_folder, 'serverless_s3_event_filtering.yml')
    sc_file_full_path = os.path.join(get_test_files_folder, 'serverless_application_code_module.py')
    event_filtering_manager = EventFilteringManagerCls(infrastruc_code_dict,
                                                       's3',
                                                       handler,
                                                       sc_file_full_path)
    result = event_filtering_manager.get_event_filtering_result(var, 'unresolved')
    assert result == expected_result

@pytest.mark.parametrize('sc_file, expected_result', [
    ('httphandler_assign_filter_false.py', False),
    ('httphandler_assign_filter_true.py', True),
    ('httphandler_literal_filter_false.py', False),
    ('httphandler_literal_filter_true.py', True),
])
def test_analyse_event_filtering(get_test_files_folder,
                                 sc_file,
                                 expected_result):
    infrastruc_code_dict = extract_dict_from_yaml(get_test_files_folder, 'serverless_s3_event_filtering.yml')
    # Process source code file
    sc_file_full_path = os.path.join(get_test_files_folder, sc_file)
    api_call_ast_node = extract_api_call_ast_node(sc_file_full_path)
    # Call function under test
    event_filtering_res = analyse_event_filtering('s3',
                                                  [{'Key': '2'}],
                                                  api_call_ast_node,
                                                  infrastruc_code_dict,
                                                  'onS3Upload',
                                                  sc_file_full_path)
    assert event_filtering_res == expected_result
