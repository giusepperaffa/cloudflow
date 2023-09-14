# =========================================
# Import Python Modules (Stanadard Library)
# =========================================
import os
import pytest
import yaml

# ================
# Module Variables
# ================
repo_full_path = os.sep.join(os.path.realpath(__file__).split(os.sep)[:-2])

# ========================
# Fixtures (Session Scope)
# ========================
@pytest.fixture(scope='session')
def get_main_test_files_folder():
    return os.path.join(repo_full_path, 'tests', 'test-files')

# =========================
# Fixtures (Function Scope)
# =========================
@pytest.fixture
def get_yaml_test_file_dict(get_main_test_files_folder, request):
    # Obtain Marker object with built-in fixture request
    m = request.node.get_closest_marker('yaml_test_file')
    if m and len(m.args) == 2:
        # Process first marker parameter
        test_files_folder = os.path.join(get_main_test_files_folder,
                                         os.path.splitext(os.path.basename(m.args[0]))[0].split('_')[1])
        test_file = os.path.join(test_files_folder, m.args[1])
        with open(test_file, mode='r') as file_obj:
            extracted_dict = yaml.load(file_obj, Loader=yaml.BaseLoader)
        return extracted_dict
    else:
        raise ValueError('Inconsistency detected - Check passed parameters')
