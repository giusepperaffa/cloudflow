# =========================================
# Import Python Modules (Stanadard Library)
# =========================================
import os
import pytest
import yaml
import sys

# =========================
# Update Python Search Path
# =========================
repo_full_path = os.sep.join(os.path.realpath(__file__).split(os.sep)[:-2])
sys.path.append(repo_full_path)

# ========================================
# Import Python Modules (Project-specific)
# ========================================
from cloudflow.modules.customresolverreslib import YAMLResolverCls

# ========
# Fixtures
# ========
@pytest.fixture
def get_test_files_folder():
    return os.path.join(repo_full_path, 'tests', \
        'test-files', os.path.splitext(__file__.split('_')[1])[0])

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
    assert resolved_yaml_dict['provider']['iamRoleStatements'] == 'Unknown'

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
