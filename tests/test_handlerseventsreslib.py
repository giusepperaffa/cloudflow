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
from cloudflow.modules.handlerseventsreslib import HandlersEventsIdentifierCls

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
def test_one_handler_only(get_test_files_folder):
    test_file = os.path.join(get_test_files_folder, 'serverless_one_handler_only.yml')
    with open(test_file, mode='r') as file_obj:
        extracted_dict = yaml.load(file_obj, Loader=yaml.BaseLoader)
        he_identifier_obj = HandlersEventsIdentifierCls(extracted_dict)
    assert he_identifier_obj.get_num_of_events() == 0
    assert he_identifier_obj.get_num_of_handlers() == 1

def test_one_handler_one_event(get_test_files_folder):
    test_file = os.path.join(get_test_files_folder, 'serverless_one_handler_one_event.yml')
    with open(test_file, mode='r') as file_obj:
        extracted_dict = yaml.load(file_obj, Loader=yaml.BaseLoader)
        he_identifier_obj = HandlersEventsIdentifierCls(extracted_dict)
    assert he_identifier_obj.get_num_of_events() == 1
    assert he_identifier_obj.get_num_of_handlers() == 1
