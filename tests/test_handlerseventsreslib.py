# =========================================
# Import Python Modules (Stanadard Library)
# =========================================
import os
import pytest
import yaml

# ========================================
# Import Python Modules (Project-specific)
# ========================================
from cloudflow.modules.handlerseventsreslib import HandlersEventsIdentifierCls

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
    assert he_identifier_obj.handlers_dict['hello'] == \
        set([('httpApi', 'get')])

def test_handlers_with_and_without_events(get_test_files_folder):
    test_file = os.path.join(get_test_files_folder, 'serverless_handlers_with_and_without_events.yml')
    with open(test_file, mode='r') as file_obj:
        extracted_dict = yaml.load(file_obj, Loader=yaml.BaseLoader)
        he_identifier_obj = HandlersEventsIdentifierCls(extracted_dict)
    assert he_identifier_obj.get_num_of_events() == 2
    assert he_identifier_obj.get_num_of_handlers() == 3
    assert he_identifier_obj.handlers_dict['auth'] == set()
    assert he_identifier_obj.handlers_dict['privateEndpoint'] == \
        set([('http', 'post')])
    assert he_identifier_obj.handlers_dict['publicEndpoint'] == \
        set([('http', 'post')])

@pytest.mark.parametrize("test_file, expected_num_of_events, expected_num_of_handlers", [\
        ('serverless_two_handlers_two_events.yml', 2, 2),
        ('serverless_five_handlers_five_events.yml', 5, 5),
    ])
def test_multi_handlers_and_events(get_test_files_folder, test_file, \
    expected_num_of_events, expected_num_of_handlers):
    test_file = os.path.join(get_test_files_folder, test_file)
    with open(test_file, mode='r') as file_obj:
        extracted_dict = yaml.load(file_obj, Loader=yaml.BaseLoader)
        he_identifier_obj = HandlersEventsIdentifierCls(extracted_dict)
    assert he_identifier_obj.get_num_of_events() == expected_num_of_events
    assert he_identifier_obj.get_num_of_handlers() == expected_num_of_handlers

def test_multi_events_from_same_service(get_test_files_folder):
    test_file = os.path.join(get_test_files_folder, 'serverless_multi_events_from_same_service.yml')
    with open(test_file, mode='r') as file_obj:
        extracted_dict = yaml.load(file_obj, Loader=yaml.BaseLoader)
        he_identifier_obj = HandlersEventsIdentifierCls(extracted_dict)
    assert he_identifier_obj.get_num_of_events() == 7
    assert he_identifier_obj.get_num_of_handlers() == 6
    assert he_identifier_obj.handlers_dict['create'] == set([('http', 'post')])
    assert he_identifier_obj.handlers_dict['bucket'] == \
        set([('s3', 'ObjectCreated:*'), ('s3', 'ObjectRemoved:*')])

def test_step_function_event(get_test_files_folder):
    test_file = os.path.join(get_test_files_folder, 'serverless_step_function_event.yml')
    with open(test_file, mode='r') as file_obj:
        extracted_dict = yaml.load(file_obj, Loader=yaml.BaseLoader)
        he_identifier_obj = HandlersEventsIdentifierCls(extracted_dict)
    assert he_identifier_obj.get_num_of_events() == 1
    assert he_identifier_obj.get_num_of_handlers() == 3

def test_one_event_via_string(get_test_files_folder):
    test_file = os.path.join(get_test_files_folder, 'serverless_two_handlers_two_events.yml')
    with open(test_file, mode='r') as file_obj:
        extracted_dict = yaml.load(file_obj, Loader=yaml.BaseLoader)
        he_identifier_obj = HandlersEventsIdentifierCls(extracted_dict)
    assert he_identifier_obj.get_num_of_handlers() == 2
    assert he_identifier_obj.get_num_of_events() == 2
    assert he_identifier_obj.handlers_dict['rateHandler'] == \
        set([('schedule', 'rate(1 minute)')])
    assert he_identifier_obj.handlers_dict['cronHandler'] == \
        set([('schedule', 'cron(0/2 * ? * MON-FRI *)')])

def test_multi_events_via_strings(get_test_files_folder):
    test_file = os.path.join(get_test_files_folder, 'serverless_multi_events_from_same_service_via_strings.yml')
    with open(test_file, mode='r') as file_obj:
        extracted_dict = yaml.load(file_obj, Loader=yaml.BaseLoader)
        he_identifier_obj = HandlersEventsIdentifierCls(extracted_dict)
    assert he_identifier_obj.get_num_of_handlers() == 2
    assert he_identifier_obj.get_num_of_events() == 2
    assert he_identifier_obj.handlers_dict['cloudwatchLogsSubscriber'] == \
        set([('cloudwatchLog', '/aws/lambda/some-service-${self:provider.stage}-someFunction1'), \
             ('cloudwatchLog', '/aws/lambda/some-service-${self:provider.stage}-someFunction2')])
   