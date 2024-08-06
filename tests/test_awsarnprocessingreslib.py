# ========================================
# Import Python Modules (Standard Library)
# ========================================
import pytest

# ========================================
# Import Python Modules (Project-specific)
# ========================================
from cloudflow.utils.awsarnprocessingreslib import AWSARNManagerCls

# ========
# Fixtures
# ========
@pytest.fixture
def get_valid_arn():
    return 'arn:aws:dynamodb:eu-central-1:*:table/aws-python-project-test-table'

@pytest.fixture
def get_invalid_arn():
    return 'arn::invalid' 

# ==============
# Test Functions
# ==============
def test_valid_arn(get_valid_arn):
    # Create instance of AWSARNManagerCls
    aws_arn_manager = AWSARNManagerCls(get_valid_arn)
    # Check whether the passed ARN is valid
    assert aws_arn_manager.is_valid() == True
    # Check the extracted ARN fields
    assert aws_arn_manager.get_partition() == 'aws'
    assert aws_arn_manager.get_service() == 'dynamodb'
    assert aws_arn_manager.get_region() == 'eu-central-1'
    assert aws_arn_manager.get_account_id() == '*'
    assert aws_arn_manager.get_resource_id() == 'table/aws-python-project-test-table'

def test_invalid_arn(get_invalid_arn):
    # Create instance of AWSARNManagerCls
    aws_arn_manager = AWSARNManagerCls(get_invalid_arn)
    # Check whether the passed ARN is valid
    assert aws_arn_manager.is_valid() == False
    # Check the extracted ARN fields
    for flt_elem in (elem for elem in dir(aws_arn_manager) if elem.startswith('get')):
        assert getattr(aws_arn_manager, flt_elem)() == ''
    