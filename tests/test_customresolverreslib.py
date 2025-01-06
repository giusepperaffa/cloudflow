# =========================================
# Import Python Modules (Stanadard Library)
# =========================================
import os
import pytest
import shutil

# ========================================
# Import Python Modules (Project-specific)
# ========================================
from cloudflow.utils.fileprocessingreslib import extract_dict_from_yaml
from cloudflow.modules.customresolverreslib import YAMLResolverCls
from cloudflow.modules.customresolverreslib import resolve_value_from_yaml
from cloudflow.modules.customresolverreslib import check_if_resolved
from cloudflow.modules.customresolverreslib import ExtFilesManagerCls

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
    yaml_resolver_obj = YAMLResolverCls(test_file, False)
    resolved_yaml_dict = yaml_resolver_obj.resolve_yaml('dict')
    assert isinstance(resolved_yaml_dict, dict)

def test_unresolved_value_with_option(get_test_files_folder, get_multi_unresolved_values_file):
    test_file = os.path.join(get_test_files_folder, get_multi_unresolved_values_file)
    yaml_resolver_obj = YAMLResolverCls(test_file, False)
    resolved_yaml_dict = yaml_resolver_obj.resolve_yaml('dict')
    assert resolved_yaml_dict['provider']['stage'] == 'stage'

def test_unresolvable_value(get_test_files_folder, get_multi_unresolved_values_file):
    test_file = os.path.join(get_test_files_folder, get_multi_unresolved_values_file)
    yaml_resolver_obj = YAMLResolverCls(test_file, False)
    resolved_yaml_dict = yaml_resolver_obj.resolve_yaml('dict')
    assert resolved_yaml_dict['provider']['environment']['ALERT_PROCESS_ERRORS'] == \
        '${opt:alertProcessErrors, self:custom.defaultAlertProcessErrors}'

def test_nested_unresolved_value(get_test_files_folder, get_multi_unresolved_values_file):
    test_file = os.path.join(get_test_files_folder, get_multi_unresolved_values_file)
    yaml_resolver_obj = YAMLResolverCls(test_file, False)
    resolved_yaml_dict = yaml_resolver_obj.resolve_yaml('dict')
    assert resolved_yaml_dict['provider']['environment']['CONFIG_FILE'] == \
        './configs/stage/config.cfg'

def test_concatenated_unresolved_value(get_test_files_folder, get_multi_unresolved_values_file):
    test_file = os.path.join(get_test_files_folder, get_multi_unresolved_values_file)
    yaml_resolver_obj = YAMLResolverCls(test_file, False)
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

def test_ext_file_to_resolve(get_test_files_folder):
    test_file = os.path.join(get_test_files_folder, 'serverless_unresolved_ext_file.yml')
    ext_files_manager_obj = ExtFilesManagerCls(test_file)
    resolved_yaml_dict = ext_files_manager_obj.resolve_ext_files()
    # Check types (of and within returned data structure)
    assert isinstance(resolved_yaml_dict, dict)
    assert isinstance(resolved_yaml_dict['resources'], list)
    # Check returned data structure consistency
    assert len(resolved_yaml_dict['resources']) == 2
    extracted_results = ['BillingMode' in resource['Resources']['EventsTable']['Properties']
                         for resource in resolved_yaml_dict['resources']]
    assert len(list(filter(lambda x: x == True, extracted_results))) == 1

def test_ext_file_to_resolve_integration(get_test_files_folder):
    test_file = os.path.join(get_test_files_folder, 'serverless_unresolved_ext_file.yml')
    test_file_copy = os.path.join(get_test_files_folder, 'serverless_unresolved_ext_file_COPY.yml')
    # Copy test file as the test requires modifying it
    shutil.copy2(test_file, test_file_copy)
    yaml_resolver = YAMLResolverCls(test_file_copy)
    resolved_yaml_dict = yaml_resolver.resolve_yaml()
    assert len(resolved_yaml_dict['resources']) == 2
    extracted_results = ['ProvisionedThroughput' in resource['Resources']['EventsTable']['Properties']
                         for resource in resolved_yaml_dict['resources']]
    assert len(list(filter(lambda x: x == True, extracted_results))) == 1
    # Remove modified test file
    os.remove(test_file_copy)

@pytest.mark.parametrize('yaml_file, unresolved_value, expected_result', [
    ('serverless_unresolved_value_ext_file_simple.yml',
     '${file(ext_file_prod_config.yml):securityGroupId}',
     'sg-035524dc93c6d1bf8'),
     ('serverless_unresolved_value_ext_file_nested.yml',
      '${file(ext_file_config.yml):${self:provider.stage}.LAMBDA_MEMORY_SIZE}',
      '256')
])
def test_value_from_ext_file(get_test_files_folder,
                             yaml_file,
                             unresolved_value,
                             expected_result):
    test_file = os.path.join(get_test_files_folder, yaml_file)
    ext_files_manager_obj = ExtFilesManagerCls(test_file)
    assert ext_files_manager_obj.resolve_value_from_ext_file(unresolved_value) == expected_result

@pytest.mark.parametrize('yaml_file, expected_result', [
    ('serverless_unresolved_value_ext_file_simple.yml', 'sg-035524dc93c6d1bf8'),
    ('serverless_unresolved_value_ext_file_nested.yml', '256')
])
def test_unresolved_value_within_file(get_test_files_folder,
                                      yaml_file,
                                      expected_result):
    test_file = os.path.join(get_test_files_folder, yaml_file)
    yaml_resolver = YAMLResolverCls(test_file, False)
    resolved_yaml_dict = yaml_resolver.resolve_yaml()
    if yaml_file.endswith('simple.yml'):
        assert isinstance(resolved_yaml_dict['provider']['vpc']['securityGroupIds'], list)
        assert resolved_yaml_dict['provider']['vpc']['securityGroupIds'][0] == expected_result
    elif yaml_file.endswith('nested.yml'):
        assert resolved_yaml_dict['provider']['memorySize'] == expected_result
