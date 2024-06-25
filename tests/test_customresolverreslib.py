# =========================================
# Import Python Modules (Stanadard Library)
# =========================================
import os
import pytest

# ========================================
# Import Python Modules (Project-specific)
# ========================================
from cloudflow.utils.fileprocessingreslib import extract_dict_from_yaml
from cloudflow.modules.customresolverreslib import YAMLResolverCls
from cloudflow.modules.customresolverreslib import resolve_value_from_yaml
from cloudflow.modules.customresolverreslib import check_if_resolved

# ========
# Fixtures
# ========
@pytest.fixture
def get_test_files_folder(get_main_test_files_folder):
    return os.path.join(get_main_test_files_folder,
                        os.path.splitext(os.path.basename(__file__))[0].split('_')[1])

@pytest.fixture
def get_multi_unresolved_values_file():
    return 'serverless_multi_unresolved_values.yml'

# ==============
# Test Functions
# ==============
def test_returned_type(get_test_files_folder, get_multi_unresolved_values_file):
    test_file = os.path.join(get_test_files_folder, get_multi_unresolved_values_file)
    yaml_resolver_obj = YAMLResolverCls(test_file)
    resolved_yaml_dict = yaml_resolver_obj.resolve_yaml('dict')
    assert isinstance(resolved_yaml_dict, dict)

def test_unresolved_value_with_option(get_test_files_folder, get_multi_unresolved_values_file):
    test_file = os.path.join(get_test_files_folder, get_multi_unresolved_values_file)
    yaml_resolver_obj = YAMLResolverCls(test_file)
    resolved_yaml_dict = yaml_resolver_obj.resolve_yaml('dict')
    assert resolved_yaml_dict['provider']['stage'] == 'stage'

def test_unresolved_value_within_file(get_test_files_folder, get_multi_unresolved_values_file):
    test_file = os.path.join(get_test_files_folder, get_multi_unresolved_values_file)
    yaml_resolver_obj = YAMLResolverCls(test_file)
    resolved_yaml_dict = yaml_resolver_obj.resolve_yaml('dict')
    assert resolved_yaml_dict['provider']['iamRoleStatements'] == 'file(./configs/stage/iam.yml)'

def test_unresolvable_value(get_test_files_folder, get_multi_unresolved_values_file):
    test_file = os.path.join(get_test_files_folder, get_multi_unresolved_values_file)
    yaml_resolver_obj = YAMLResolverCls(test_file)
    resolved_yaml_dict = yaml_resolver_obj.resolve_yaml('dict')
    assert resolved_yaml_dict['provider']['environment']['ALERT_PROCESS_ERRORS'] == \
        '${opt:alertProcessErrors, self:custom.defaultAlertProcessErrors}'

def test_nested_unresolved_value(get_test_files_folder, get_multi_unresolved_values_file):
    test_file = os.path.join(get_test_files_folder, get_multi_unresolved_values_file)
    yaml_resolver_obj = YAMLResolverCls(test_file)
    resolved_yaml_dict = yaml_resolver_obj.resolve_yaml('dict')
    assert resolved_yaml_dict['provider']['environment']['CONFIG_FILE'] == \
        './configs/stage/config.cfg'

def test_concatenated_unresolved_value(get_test_files_folder, get_multi_unresolved_values_file):
    test_file = os.path.join(get_test_files_folder, get_multi_unresolved_values_file)
    yaml_resolver_obj = YAMLResolverCls(test_file)
    resolved_yaml_dict = yaml_resolver_obj.resolve_yaml('dict')
    assert resolved_yaml_dict['functions']['cloudwatchLogsSubscriber']['events'][0]['cloudwatchLog'] == \
        '/aws/lambda/some-service-stage-someFunction1'
    assert resolved_yaml_dict['functions']['cloudwatchLogsSubscriber']['events'][1]['cloudwatchLog'] == \
        '/aws/lambda/some-service-stage-someFunction2'

@pytest.mark.parametrize('test_value, expected_result', [
    ('arn:aws:s3:::${self:custom.settings.BUCKET_NAME}/*',
     'arn:aws:s3:::aws-python-project-test-bucket/*'),
     ('arn:aws:dynamodb:${self:provider.region}:*:table/${self:custom.settings.DYNAMODB_TABLE}',
      'arn:aws:dynamodb:eu-central-1:*:table/aws-python-project-test-table')
])
def test_unresolved_resources(get_test_files_folder, test_value, expected_result):
    config_dict = extract_dict_from_yaml(get_test_files_folder, 'serverless_unresolved_resources.yml')
    assert expected_result == resolve_value_from_yaml(test_value, config_dict)

@pytest.mark.parametrize('test_value, expected_result', [
    ('${self:service}', 'StepFuncBatch')
])
def test_unresolved_values_no_nested(get_test_files_folder, test_value, expected_result):
    config_dict = extract_dict_from_yaml(get_test_files_folder, 'serverless_unresolved_values_no_nested.yml')
    assert expected_result == resolve_value_from_yaml(test_value, config_dict)

@pytest.mark.parametrize('test_value, expected_result', [
    ('provider.region', True),
    ('${self:provider.region}', False),
    (['${self:provider.region}', 'provider.region'], False),
    (['provider.region', 'provider.region'], True),
    (['${self:provider.region}', '${self:provider.region}'], False)
])
def test_check_if_resolved(test_value, expected_result):
    assert expected_result == check_if_resolved(test_value)
