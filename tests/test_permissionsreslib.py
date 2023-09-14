# =========================================
# Import Python Modules (Stanadard Library)
# =========================================
import os
import pytest
import yaml

# ========================================
# Import Python Modules (Project-specific)
# ========================================
from cloudflow.modules.permissionsreslib import PermissionsIdentifierCls

# ==============
# Test Functions
# ==============
@pytest.mark.yaml_test_file(__file__, 'serverless_one_service_cf_resource_syntax.yml')
def test_one_service_cf_resource_syntax(get_yaml_test_file_dict):
    perm_identifier_obj = PermissionsIdentifierCls(get_yaml_test_file_dict)
    assert perm_identifier_obj.get_num_of_services() == 1
    assert perm_identifier_obj.perm_dict['dynamodb'] == \
        set(['Query', 'Scan', 'GetItem', 'PutItem', 'UpdateItem', 'DeleteItem'])
    assert len(perm_identifier_obj.perm_res_dict) == 1
    assert len(list(perm_identifier_obj.perm_res_dict.values())[0]) == 6
    assert set(list(perm_identifier_obj.perm_res_dict.values())[0]) == \
        set([('dynamodb', 'Query'), ('dynamodb', 'Scan'), ('dynamodb', 'GetItem'), \
             ('dynamodb', 'PutItem'), ('dynamodb', 'UpdateItem'), ('dynamodb', 'DeleteItem')])

@pytest.mark.yaml_test_file(__file__, 'serverless_one_service_arn_resource_syntax.yml')
def test_one_service_arn_resource_syntax(get_yaml_test_file_dict):
    perm_identifier_obj = PermissionsIdentifierCls(get_yaml_test_file_dict)
    assert perm_identifier_obj.get_num_of_services() == 1
    assert perm_identifier_obj.perm_dict['dynamodb'] == \
        set(['Query', 'Scan', 'GetItem', 'PutItem', 'UpdateItem', 'DeleteItem'])
    assert len(perm_identifier_obj.perm_res_dict) == 1
    assert len(list(perm_identifier_obj.perm_res_dict.values())[0]) == 6

@pytest.mark.yaml_test_file(__file__, 'serverless_two_services.yml')
def test_two_services(get_yaml_test_file_dict):
    perm_identifier_obj = PermissionsIdentifierCls(get_yaml_test_file_dict)
    assert perm_identifier_obj.get_num_of_services() == 2
    assert len(perm_identifier_obj.perm_dict['dynamodb']) == 7
    assert perm_identifier_obj.perm_dict['s3'] == set(['*'])
    assert len(perm_identifier_obj.perm_res_dict) == 2
    assert set([('s3', '*')]) in list(perm_identifier_obj.perm_res_dict.values())

@pytest.mark.yaml_test_file(__file__, 'serverless_iam_old_syntax_one_service.yml')
def test_iam_old_syntax_one_service(get_yaml_test_file_dict):
    perm_identifier_obj = PermissionsIdentifierCls(get_yaml_test_file_dict)
    assert perm_identifier_obj.get_num_of_services() == 1
    assert perm_identifier_obj.perm_dict['s3'] == set(['Get*', 'List*'])
    assert '*' in perm_identifier_obj.perm_res_dict
    assert ('s3', 'Get*') in perm_identifier_obj.perm_res_dict['*']

@pytest.mark.yaml_test_file(__file__, 'serverless_iam_requiring_resolution.yml')
def test_iam_requiring_resolution(get_yaml_test_file_dict):
    perm_identifier_obj = PermissionsIdentifierCls(get_yaml_test_file_dict)
    assert perm_identifier_obj.get_num_of_services() == 1
    assert perm_identifier_obj.perm_dict['undefined'] == set(['${file(${self:custom.iam.${self:provider.stage}})}'])
    assert len(perm_identifier_obj.perm_res_dict) == 1
    assert 'undefined' in perm_identifier_obj.perm_res_dict
    assert perm_identifier_obj.perm_res_dict['undefined'] == set(['${file(${self:custom.iam.${self:provider.stage}})}'])

@pytest.mark.yaml_test_file(__file__, 'serverless_multi_services_resources.yml')
def test_multi_services_resources(get_yaml_test_file_dict):
    perm_identifier_obj = PermissionsIdentifierCls(get_yaml_test_file_dict)
    assert perm_identifier_obj.get_num_of_services() == 3
    assert perm_identifier_obj.perm_dict['s3'] == set(['*'])
    assert perm_identifier_obj.perm_dict['rekognition'] == set(['*'])
    assert perm_identifier_obj.perm_dict['dynamodb'] == \
        set(['Query', 'Scan', 'GetItem', 'PutItem', 'UpdateItem', 'DeleteItem'])
    assert len(perm_identifier_obj.perm_res_dict) == 4
    assert perm_identifier_obj.perm_res_dict['*'] == set([('rekognition', '*')])

@pytest.mark.yaml_test_file(__file__, 'serverless_iam_old_syntax_multi_services_resources.yml')
def test_iam_old_syntax_multi_services_resources(get_yaml_test_file_dict):
    perm_identifier_obj = PermissionsIdentifierCls(get_yaml_test_file_dict)
    assert perm_identifier_obj.get_num_of_services() == 2
    assert perm_identifier_obj.perm_dict['s3'] == \
        set(['ListBucket', 'GetObject', 'PutObject'])
    assert perm_identifier_obj.perm_dict['rds'] == \
        set(['DownloadCompleteDBLogFile', 'DescribeDBLogFiles'])
    assert len(perm_identifier_obj.perm_res_dict) == 4
    assert '*' in perm_identifier_obj.perm_res_dict
    assert set([('s3', 'GetObject'), ('s3', 'PutObject')]) in \
        list(perm_identifier_obj.perm_res_dict.values())
