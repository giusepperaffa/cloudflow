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
from cloudflow.modules.permissionsreslib import PermissionsIdentifierCls

# ========
# Fixtures
# ========
@pytest.fixture
def get_test_files_folder():
    return os.path.join(repo_full_path, 'tests', \
        'test-files', os.path.splitext(__file__.split('_')[1])[0])

# ==============
# Test Functions
# ==============
def test_one_service_cf_resource_syntax(get_test_files_folder):
    test_file = os.path.join(get_test_files_folder, 'serverless_one_service_cf_resource_syntax.yml')
    with open(test_file, mode='r') as file_obj:
        extracted_dict = yaml.load(file_obj, Loader=yaml.BaseLoader)
        perm_identifier_obj = PermissionsIdentifierCls(extracted_dict)
    assert perm_identifier_obj.get_num_of_services() == 1
    assert perm_identifier_obj.perm_dict['dynamodb'] == \
        set(['Query', 'Scan', 'GetItem', 'PutItem', 'UpdateItem', 'DeleteItem'])

def test_one_service_arn_resource_syntax(get_test_files_folder):
    test_file = os.path.join(get_test_files_folder, 'serverless_one_service_arn_resource_syntax.yml')
    with open(test_file, mode='r') as file_obj:
        extracted_dict = yaml.load(file_obj, Loader=yaml.BaseLoader)
        perm_identifier_obj = PermissionsIdentifierCls(extracted_dict)
    assert perm_identifier_obj.get_num_of_services() == 1
    assert perm_identifier_obj.perm_dict['dynamodb'] == \
        set(['Query', 'Scan', 'GetItem', 'PutItem', 'UpdateItem', 'DeleteItem'])
