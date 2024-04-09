# ========================================
# Import Python Modules (Standard Library)
# ========================================
import pytest

# ========================================
# Import Python Modules (Project-specific)
# ========================================
from cloudflow.modules.pluginprocessingreslib import PluginManagerCls

# ==============
# Test Functions
# ==============
@pytest.mark.yaml_test_file(__file__, 'serverless_iam_roles_per_function_basic.yml')
def test_iam_roles_per_function_basic(get_yaml_test_file_dict):
    plugin_manager = PluginManagerCls(get_yaml_test_file_dict)
    extracted_info = plugin_manager.plugin_extracted_info
    plugin_data = extracted_info.plugin_info
    assert extracted_info.has_config_params_for_plugin('IAMRolesPerFunction')
    assert extracted_info.has_handlers_permissions()
    for handler, value in plugin_data['config']['IAMRolesPerFunction']['Override']:
        assert value
    assert 'dynamodb:GetItem' in plugin_data['handlers']['func1']
    assert 'dynamodb:PutItem' in plugin_data['handlers']['func2']

@pytest.mark.yaml_test_file(__file__, 'serverless_iam_roles_per_function_empty.yml')
def test_iam_roles_per_function_empty(get_yaml_test_file_dict):
    plugin_manager = PluginManagerCls(get_yaml_test_file_dict)
    extracted_info = plugin_manager.plugin_extracted_info
    plugin_data = extracted_info.plugin_info
    assert extracted_info.has_config_params_for_plugin('IAMRolesPerFunction')
    # No handler-level permission is extracted in this case
    assert not extracted_info.has_handlers_permissions()
    # Since the test file relies on the default plugin configuration,
    # the override behaviour is enabled.   
    for handler, value in plugin_data['config']['IAMRolesPerFunction']['Override']:
        assert value

@pytest.mark.yaml_test_file(__file__, 'serverless_iam_roles_per_function_with_inherit.yml')
def test_iam_roles_per_function_with_inherit(get_yaml_test_file_dict):
    plugin_manager = PluginManagerCls(get_yaml_test_file_dict)
    extracted_info = plugin_manager.plugin_extracted_info
    plugin_data = extracted_info.plugin_info
    assert extracted_info.has_config_params_for_plugin('IAMRolesPerFunction')
    assert extracted_info.has_handlers_permissions()
    # Since the inherit option is used in the test file for one of
    # the two handlers, their override configuration is different.
    for handler, value in plugin_data['config']['IAMRolesPerFunction']['Override']:
        if handler == 'func1':
            assert not value
        elif handler == 'func2':
            assert value
        else:
            raise ValueError('--- No expected handler detected ---')
    assert 'dynamodb:GetItem' in plugin_data['handlers']['func1']
    assert 'dynamodb:PutItem' in plugin_data['handlers']['func2']

@pytest.mark.yaml_test_file(__file__, 'serverless_iam_roles_per_function_custom_config.yml')
def test_iam_roles_per_function_custom_config(get_yaml_test_file_dict):
    plugin_manager = PluginManagerCls(get_yaml_test_file_dict)
    extracted_info = plugin_manager.plugin_extracted_info
    plugin_data = extracted_info.plugin_info
    assert extracted_info.has_config_params_for_plugin('IAMRolesPerFunction')
    assert extracted_info.has_handlers_permissions()
    # Because of the custom plugin configuration, the override
    # configuration is always disabled. 
    for handler, value in plugin_data['config']['IAMRolesPerFunction']['Override']:
        assert not value
    assert 'dynamodb:GetItem' in plugin_data['handlers']['func1']
    assert 'dynamodb:PutItem' in plugin_data['handlers']['func2']

@pytest.mark.yaml_test_file(__file__, 'serverless_iam_roles_per_function_basic.yml')
def test_plugin_config_params_extraction(get_yaml_test_file_dict):
    plugin_manager = PluginManagerCls(get_yaml_test_file_dict)
    extracted_info = plugin_manager.plugin_extracted_info
    config_params = extracted_info.get_config_params_for_plugin('IAMRolesPerFunction')
    expected_result = {'Override': {('func1', True), ('func2', True)}}
    assert config_params == expected_result
    # Test with not existing plugin
    config_params = extracted_info.get_config_params_for_plugin('NotExisting')
    assert config_params is None

@pytest.mark.yaml_test_file(__file__, 'serverless_iam_roles_per_function_basic.yml')
def test_handler_permissions_extraction(get_yaml_test_file_dict):
    plugin_manager = PluginManagerCls(get_yaml_test_file_dict)
    extracted_info = plugin_manager.plugin_extracted_info
    handler_permissions = extracted_info.get_permissions_for_handler('func1')
    expected_result = {'dynamodb:GetItem'}
    assert handler_permissions == expected_result
    # Test with cloud service filter. Expected result is unaltered,
    # as the only service in the configuration file is dynamodb.
    handler_permissions = extracted_info.get_permissions_for_handler('func1', 'dynamodb')
    assert handler_permissions == expected_result
    # Test with cloud service filter. Expected result is an empty
    # set, as there are no permissions for the specified service.
    handler_permissions = extracted_info.get_permissions_for_handler('func1', 's3')
    assert handler_permissions == set()
    # Test with keep_service_name parameter set to False
    handler_permissions = extracted_info.get_permissions_for_handler('func1',
                                                                     'dynamodb',
                                                                     False)
    expected_result = {'GetItem'}
    assert handler_permissions == expected_result

@pytest.mark.yaml_test_file(__file__, 'serverless_step_functions_basic.yml')
def test_step_functions_basic(get_yaml_test_file_dict):
    plugin_manager = PluginManagerCls(get_yaml_test_file_dict)
    extracted_info = plugin_manager.plugin_extracted_info
    plugin_data = extracted_info.plugin_info
    # The model for the plugin serverless-step-functions
    # extracts neither configuration parameters nor
    # handler-level permissions.
    assert not extracted_info.has_config_params_for_plugin('StepFunctions')
    assert not extracted_info.has_handlers_permissions()
    # Check extracted event-related information
    assert extracted_info.has_events_info()
    assert plugin_data['events']['RecordAC'] == {('http', 'POST')}
    assert plugin_data['events']['RecordDB'] == {('http', 'POST')}
    assert plugin_data['events']['InviteSlack'] == {('http', 'POST')}
