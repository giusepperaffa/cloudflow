# ========================================
# Import Python Modules (Standard Library)
# ========================================
import os
import pytest

# ========================================
# Import Python Modules (Project-specific)
# ========================================
from cloudflow.utils.astprocessingreslib import get_module_func_ast_nodes

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
def test_get_module_func_ast_nodes(get_test_files_folder):
    result = get_module_func_ast_nodes(os.path.join(get_test_files_folder, 'handlers.py'))
    assert isinstance(result, set) and (len(result) == 2)
    assert set(['my_func', 'my_func_with_nested_func']) == {node.name for node in result}
    assert set([1, 4]) == {node.lineno for node in result}
