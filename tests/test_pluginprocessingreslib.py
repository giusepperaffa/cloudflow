# =========================================
# Import Python Modules (Stanadard Library)
# =========================================
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