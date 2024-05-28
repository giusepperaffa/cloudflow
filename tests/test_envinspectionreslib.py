# ========================================
# Import Python Modules (Standard Library)
# ========================================
import os
import pytest

# ========================================
# Import Python Modules (Project-specific)
# ========================================
from cloudflow.utils.fileprocessingreslib import extract_dict_from_yaml
from cloudflow.modules.envinspectionreslib import EnvInspectionManagerCls

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
@pytest.mark.parametrize('handler, env_var, expected_result', [
    ('encrypt', 'KMS_KEY_ALIAS', 'alias/psm-dev'),
    ('encrypt', 'REGION', 'us-west-2'),
    ('encrypt', 'METADATA_AS_PARAM', 'true'),
    ('update', 'KMS_KEY_ALIAS', 'alias/psm-dev')
])
def test_provider_level_env_only(get_test_files_folder, handler, env_var, expected_result):
    infrastruc_code_dict = extract_dict_from_yaml(get_test_files_folder, 'serverless_provider_level_env_only.yml')
    env_inspection_manager = EnvInspectionManagerCls(infrastruc_code_dict,
                                                     handler,
                                                     None)
    result = env_inspection_manager.get_env_var_value(env_var)
    assert result == expected_result

@pytest.mark.parametrize('handler, env_var, expected_result', [
    ('generate', 'BIG_LAMBDA_NAME', 'bigtext-prod-big'),
    ('event_handler', 'BIG_LAMBDA_NAME', 'bigtext-prod-big')
])
def test_handler_level_env_only(get_test_files_folder, handler, env_var, expected_result):
    infrastruc_code_dict = extract_dict_from_yaml(get_test_files_folder, 'serverless_handler_level_env_only.yml')
    env_inspection_manager = EnvInspectionManagerCls(infrastruc_code_dict,
                                                     handler,
                                                     None)
    result = env_inspection_manager.get_env_var_value(env_var)
    assert result == expected_result

@pytest.mark.parametrize('handler, env_var, expected_result', [
    ('generate', 'NON_EXISTENT_NAME', None),
    ('event_handler', 'NON_EXISTENT_NAME', None)
])
def test_non_existent_env_vars(get_test_files_folder, handler, env_var, expected_result):
    infrastruc_code_dict = extract_dict_from_yaml(get_test_files_folder, 'serverless_handler_level_env_only.yml')
    env_inspection_manager = EnvInspectionManagerCls(infrastruc_code_dict,
                                                     handler,
                                                     None)
    result = env_inspection_manager.get_env_var_value(env_var)
    assert result is expected_result


@pytest.mark.parametrize('handler, env_var, expected_result', [
    ('big', 'S3_CONTENT_BUCKET', None),
    ('oauth2callback', 'WEB_APP_URL', None)
])
def test_unresolved_env_vars(get_test_files_folder, handler, env_var, expected_result):
    """
    Check the behaviour of the code when there are unresolved
    environment variables. NOTE: The results of this test
    function might change in the future if the code that
    resolves the YAML file improves.
    """
    infrastruc_code_dict = extract_dict_from_yaml(get_test_files_folder, 'serverless_handler_level_env_only.yml')
    env_inspection_manager = EnvInspectionManagerCls(infrastruc_code_dict,
                                                     handler,
                                                     None)
    result = env_inspection_manager.get_env_var_value(env_var)
    assert result is expected_result
