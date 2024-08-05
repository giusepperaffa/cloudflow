# ========================================
# Import Python Modules (Standard Library)
# ========================================
import os
import pytest

# ========================================
# Import Python Modules (Project-specific)
# ========================================
from cloudflow.utils.fileprocessingreslib import extract_dict_from_yaml
from cloudflow.modules.eventfilteringreslib import EventFilteringManagerCls

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
