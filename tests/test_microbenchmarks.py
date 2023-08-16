# ========================================
# Import Python Modules (Standard Library)
# ========================================
import csv
import pytest
import os

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.utils.fileprocessingreslib import extract_dict_from_yaml

# =================
# Module Parameters
# =================
# Folder that identifies the microbenchmark
# repository. It must be within the same
# folder as the tool repository.
mb_folder = 'cloudbench'

# ===================
# Auxiliary Functions
# ===================
def extract_mb_repo_paths():
    """
    Function that processes the configuration file
    of the microbenchmark repository and returns
    the specified repositories in a list of paths.
    NOTE: Returned paths are strings. 
    """
    return ['path/to/repo/A', '/path/to/repo/B']

def get_mb_repo_config_dict():
    """
    Function that maps the configuration file of
    the microbenchmark repository into a dictionary.
    NOTE: In case of multiple YAML files, only the
    first that is identified will be processed.
    """
    mb_repo_full_path = os.path.join(get_tool_folder_full_path(), mb_folder)
    config_file = [elem for elem in os.listdir(mb_repo_full_path)
                   if os.path.splitext(elem)[1] in ('.yml', '.yaml')][0]
    mb_repo_config_dict = extract_dict_from_yaml(mb_repo_full_path, config_file)
    return mb_repo_config_dict

def get_tool_folder_full_path():
    """
    Function that returns as a string the full
    path of the folder where the tool repository
    is stored.
    """
    return os.sep.join(os.path.dirname(__file__).split(os.sep)[:-2])
    
def process_pysa_results(mb_repo):
    """
    Function that processes the Pysa results file
    for the microbenchmark repository passed as
    input argument. It returns a list containing
    dictionaries, with each element of the list
    corresponding to a Pysa issue.
    NOTE: The returned dictionaries contain only
    sink and source-related keys. 
    """
    return [{}]

def process_expected_results(mb_repo):
    """
    Function that processes the configuration file
    of the microbenchmark repository passed as
    input argument. It returns a list containing
    dictionaries, with each element of the list
    corresponding to an expected data flow.
    """
    return [{}]

# ==============
# Test Functions
# ==============
@pytest.mark.parametrize('mb_repo_path', extract_mb_repo_paths())
def test_mb(mb_repo_path):
    pysa_results_list = process_pysa_results(mb_repo_path)
    expected_results_list = process_expected_results(mb_repo_path)
    for expected_result in expected_results_list:
        assert expected_result in pysa_results_list
