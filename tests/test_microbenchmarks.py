# ========================================
# Import Python Modules (Standard Library)
# ========================================
import csv
import pytest
import os
import re

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.utils.fileprocessingreslib import extract_dict_from_yaml

# =================
# Module Parameters
# =================
# Folder that identifies the microbenchmarks'
# repository. It must be within the same
# folder as the tool repository.
mb_folder = 'cloudbench'
# The names of the analysis folders generated
# by CloudFlow start with the following string,
# which is used to aid their identification.
analysis_folder_id = 'cloudflow-analysis'
# Folder within a CloudFlow analysis folder
# containing the Pysa results file.
pysa_results_folder_name = 'pysa-runs'

# ===================
# Auxiliary Functions
# ===================
def extract_mb_repo_paths():
    """
    Function that processes the configuration file
    of the microbenchmarks' repository and returns
    the tested repositories in a list of paths
    within the microbenchmarks' repository.
    NOTE: Returned paths are strings and only tested
    microbenchmarks are returned.
    """
    # Auxiliary list init
    mb_repo_paths = list()
    mb_repo_config_dict = get_mb_repo_config_dict()
    # The following cycle processes the microbenchmarks'
    # repository configuration to obtain the path of all
    # the contained repositories.
    for mb_category in mb_repo_config_dict:
        if mb_category in ('inter-procedural', 'intra-procedural'):
            for cloud_service in mb_repo_config_dict[mb_category]:
                mb_repo_paths.extend(os.path.join(mb_category, cloud_service, repo)
                                     for repo in mb_repo_config_dict[mb_category][cloud_service].keys())
        elif mb_category == 'simple-apps':
            mb_repo_paths.extend(os.path.join(mb_category, repo)
                                 for repo in mb_repo_config_dict[mb_category].keys())
    # The tested microbenchmarks are identified by
    # inspecting the analysis folders.
    tested_mb_repo_paths = [mb_repo_path for mb_repo_path in mb_repo_paths
                            if '-'.join([analysis_folder_id, os.path.basename(mb_repo_path)])
                            in os.listdir(get_tool_folder_full_path())]
    return tested_mb_repo_paths

def get_mb_repo_config_dict():
    """
    Function that maps the configuration file of the
    microbenchmarks' repository into a dictionary.
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
    for the specific microbenchmark repository
    passed as input argument. It returns a list
    containing dictionaries, with each element
    of the list corresponding to a Pysa issue.
    NOTE: The returned dictionaries contain only
    sink and source-related keys. In case of
    multiple CSV files, only the first that is
    identified will be processed.
    """
    # Auxiliary list init
    pysa_results_list = list()
    # Regular expression to filter results file columns
    results_reg_exp = re.compile(r'^(source|sink)', re.I)
    # Full path of folder with Pysa results file
    pysa_results_folder = os.path.join(get_tool_folder_full_path(),
                                       '-'.join([analysis_folder_id, os.path.basename(mb_repo)]),
                                       pysa_results_folder_name)
    pysa_results_file = [item for item in os.listdir(pysa_results_folder)
                         if os.path.splitext(item)[1] == '.csv'][0]
    with open(os.path.join(pysa_results_folder,
                           pysa_results_file), mode='r') as file_obj:
        reader = csv.DictReader(file_obj)
        for row in reader:
            pysa_results_list.append({key: value for key, value
                                      in row.items() if results_reg_exp.search(key) is not None})
    return pysa_results_list

def process_expected_results(mb_repo):
    """
    Function that processes the configuration file
    of the specific microbenchmark repository passed
    as input argument. It returns a list containing
    dictionaries, with each element of the list
    corresponding to an expected data flow.
    """
    # Auxiliary list init
    data_flow_list = list()
    mb_repo_config_dict = get_mb_repo_config_dict()
    try:
        mb_category, cloud_service, repo = mb_repo.split(os.sep)
        extracted_data_flow_list = mb_repo_config_dict[mb_category][cloud_service][repo]
    except KeyError:
        mb_category, repo = mb_repo.split(os.sep)
        extracted_data_flow_list = mb_repo_config_dict[mb_category][repo]
    # The data flow list extracted from the microbenchmarks'
    # configuration dictionary needs to be further processed
    # to match the format of the Pysa results.
    for data_flow_dict in extracted_data_flow_list:
        data_flow_list.append({key.replace('-', ' ').title(): value
                               for key, value in data_flow_dict['data-flow'].items()})
    return data_flow_list

# ==============
# Test Functions
# ==============
@pytest.mark.parametrize('mb_repo_path', extract_mb_repo_paths())
def test_mb(mb_repo_path):
    pysa_results_list = process_pysa_results(mb_repo_path)
    expected_results_list = process_expected_results(mb_repo_path)
    for expected_result in expected_results_list:
        assert expected_result in pysa_results_list
