# =========================================
# Import Python Modules (Stanadard Library)
# =========================================
import os
import pytest

# ================
# Module Variables
# ================
repo_full_path = os.sep.join(os.path.realpath(__file__).split(os.sep)[:-2])

# ========
# Fixtures
# ========
@pytest.fixture
def get_main_test_files_folder():
    return os.path.join(repo_full_path, 'tests', 'test-files')
