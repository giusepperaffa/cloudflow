# ========================================
# Import Python Modules (Standard Library)
# ========================================
import json
import os
import subprocess
import sys

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.utils.fileprocessingreslib import extract_dict_from_yaml

# =======
# Classes
# =======
class PysaConfigManagerCls:
    """
    Class that handles the generation of the Pysa
    configuration file.
    """
    # === Constructor ===
    def __init__(self, folders_manager, tool_config_manager):
        """
        Class constructor. Input arguments:
        -) folders_manager: Instance of folders manager
        object created with the tool's dedicated module.
        -) tool_config_manager: Instance of the tool
        configuration manager. See documentation of tool
        module toolconfigreslib.
        """
        # Attribute initialization
        self.folders_manager = folders_manager
        self.tool_config_manager = tool_config_manager
        self.virtual_env = self._get_virtual_env()
        self.pysa_config_dict = dict()
        # Auxiliary methods execution
        self.set_default_values()

    # === Protected Method ===
    def _add_other_config_values(self):
        """
        Method that adds other configuration values to
        the Pysa configuration dictionary.
        """
        self.pysa_config_dict['use_command_v2'] = True

    # === Protected Method ===
    def _add_source_code_folders(self):
        """
        Method that adds the source code folders to the
        Pysa configuration dictionary.
        """
        self.pysa_config_dict['source_directories'] = \
            [item for item in self._get_rel_paths(self.get_source_folders())]
        self._insert_top_level_repo_folder()

    # === Protected Method ===
    def _add_search_path(self,
                         config_folder='config',
                         config_file='type_annotation_config_file.yml'):
        """
        Method that adds the search path containing the
        stubs to the Pysa configuration dictionary. The
        mypy stubs for boto3 are also part of the search
        path, and are included in dedicated packages.
        Their names are extracted from a CloudFlow config
        file.
        """
        # Add folder with Pyre stubs
        self.pysa_config_dict['search_path'] = [self.pyre_stubs_folder]
        # Full path of the folder containing the CloudFlow
        # configuration file with the mypy boto3 stubs.
        config_folder_full_path = os.path.join(os.sep.join(__file__.split(os.sep)[:-2]), config_folder)
        # The CloudFlow config file is mapped into a dictionary
        # from which the mypy boto3 packages are extracted.
        config_dict = extract_dict_from_yaml(config_folder_full_path, config_file)
        for service in config_dict:
            # NOTE: Pysa expects the mypy boto3 stubs to be
            # specified in dictionaries
            config_item = {'site-package': config_dict[service]['stub_module']} 
            self.pysa_config_dict['search_path'].append(config_item)

    # === Protected Method ===
    def _add_taint_models_paths(self):
        """
        Method that adds the paths containing the taint
        models to the Pysa configuration dictionary.
        """
        # Add folder with custom Pysa models
        self.pysa_config_dict['taint_models_path'] = \
            self._get_rel_paths([self.folders_manager.pysa_models_folder])
        # Add folder with Pyre taint models
        self.pysa_config_dict['taint_models_path'].append(self.pyre_taint_models_folder)

    # === Protected Method ===
    def _get_rel_paths(self, full_paths_list):
        """
        Method that returns paths relative to the analysis
        folder. Using relative paths instead of full paths
        improves the readability of the generated Pysa
        configuration file.
        """
        return [full_path.replace(self.folders_manager.analysis_folder, '.')
                for full_path in full_paths_list]

    # === Protected Method ===
    def _insert_top_level_repo_folder(self):
        """
        Method that adds the top level repository folder
        to the source directories, if required by the
        tool configuration.
        """
        # Extract name of the analysed repository
        repo_name = os.path.basename(self.folders_manager.repo_full_path)
        # Extract top level repo folder (relative path)
        top_level_repo_folder = self._get_rel_paths([self.folders_manager.repo_full_path])[0]
        if all([top_level_repo_folder not in self.pysa_config_dict['source_directories'],
                self.tool_config_manager.get_package_mode(repo_name)]):
            self.pysa_config_dict['source_directories'].insert(0, top_level_repo_folder)

    # === Protected Method ===
    def _get_virtual_env(self):
        """
        Method that returns the virtual environment name.
        """
        # Consistency check. More details on how to determine if
        # Python is running within a virtual environment are on
        # on StackOverflow question 1871549.
        assert sys.prefix != sys.base_prefix, \
            '--- Inconsistency detected - Tool not running within a virtual environment ---'
        return os.path.basename(sys.prefix)

    # === Method ===
    def generate_config_file(self):
        """
        Method that generates the Pysa configuration file.
        """
        # Protected methods used to fill in specific parts
        # of the Pysa config dictionary are executed prior
        # to saving the dictionary (JSON file).
        self._add_source_code_folders()
        self._add_taint_models_paths()
        self._add_search_path()
        self._add_other_config_values()
        with open(os.path.join(self.folders_manager.analysis_folder,
                               self.pysa_config_file), mode='w') as file_obj:
            json.dump(self.pysa_config_dict, file_obj)

    # === Method ===
    def get_source_folders(self):
        """
        Method that obtains all the source code folders
        within the repository being analysed to be
        specified within the Pysa configuration file.
        The full paths of the folders are returned by
        the method in a list.
        """
        # Initialize returned list
        source_code_folders_list = list()
        for root, dirs, files in os.walk(self.folders_manager.repo_full_path):
            # If a repository folder contains a Python source
            # code file (a .py file), it will be included in
            # the Pysa configuration file.
            if any(os.path.splitext(item)[1] == '.py' for item in files):
                source_code_folders_list.append(root)
        return source_code_folders_list

    # === Method ===
    def set_default_values(self):
        """
        Method that sets up default values to be used
        for the generation of the configuration file.
        NOTE: Some of these default values depends on
        the installation of Pysa and Pyre.
        """
        # Default name of the configuration file
        self.pysa_config_file = '.pyre_configuration'
        # Values to be added to the configuration file
        self.pyre_taint_models_folder = os.path.join('..',
                                                     self.virtual_env,
                                                     'lib',
                                                     'pyre_check',
                                                     'taint')
        self.pyre_stubs_folder = os.path.join('..',
                                              '..',
                                              'pyre-check',
                                              'stubs')

class PysaExecManagerCls:
    """
    Class that handles the execution of Pysa.
    """
    # === Constructor ===
    def __init__(self,
                 folders_manager,
                 pysa_config_file='.pyre_configuration'):
        """
        Class constructor. Input arguments:
        -) folders_manager: Instance of folders manager
        object created with the tool's dedicated module.
        -) pysa_config_file: Pysa configuration file.
        Default value: '.pyre_configuration'.
        """
        # Attribute initialization
        self.folders_manager = folders_manager
        self.pysa_config_file = pysa_config_file

    # === Protected Method ===
    def _exec_cmd(self, cmd):
        """
        Method that executes a command passed as a string.
        """
        tool_execution = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, universal_newlines=True)
        # Provide details on the command execution
        if tool_execution.returncode == 0:
            print(f'--- Successful execution of the command: {cmd} ---')
        else:
            print(f'--- Unsuccessful execution of the command: {cmd} ---')
            print(f'--- Return code: {str(tool_execution.returncode)} ---')
            print('--- Standard error: ---')
            print(f'{tool_execution.stderr}')

    # === Protected Method ===
    def _get_cmd_dataflow_analysis(self):
        """
        Method that returns a string containing the
        command used to execute a dataflow analysis
        with Pysa.
        """
        # The command is specified in a list of strings
        cmd_list = ['pyre', 'analyze', '--save-results-to']
        cmd_list.append('./' + os.path.basename(self.folders_manager.pysa_results_folder))
        return ' '.join(cmd_list)

    # === Protected Method ===
    def _get_cmd_type_inference(self):
        """
        Method that returns a string containing the
        command used to execute an automated type
        inference with Pyre.
        """
        # The command is specified in a list of strings
        cmd_list = ['pyre', 'infer', '-i']
        return ' '.join(cmd_list)

    # === Protected Method ===
    def _restore_cur_working_folder(self):
        """
        Method that restores the initial working folder.
        """
        os.chdir(self._initial_working_folder)
        print(f'--- Working folder restored to: {os.getcwd()} ---')

    # === Protected Method ===
    def _set_cur_working_folder(self):
        """
        Method that sets the current working folder
        to the CloudFlow analysis folder and saves
        the initial working folder in a protected
        instance variable.
        """
        self._initial_working_folder = os.getcwd()
        print(f'--- Current working folder: {self._initial_working_folder} ---')
        os.chdir(self.folders_manager.analysis_folder)
        print(f'--- New working folder: {os.getcwd()} ---')
        assert os.path.isfile(os.path.join(os.getcwd(), self.pysa_config_file)), \
            '--- Inconsistency detected - Pysa configuration file not found ---'

    # === Method ===
    def exec_dataflow_analysis(self):
        """
        Method that executes a dataflow analysis with Pysa.
        """
        self._set_cur_working_folder()
        cmd = self._get_cmd_dataflow_analysis()
        self._exec_cmd(cmd)
        self._restore_cur_working_folder()

    # === Method ===
    def exec_type_inference(self):
        """
        Method that executes an automated type inference with Pyre.
        NOTE: Pyre is the static type checker Pysa is built on.
        """
        self._set_cur_working_folder()
        cmd = self._get_cmd_type_inference()
        self._exec_cmd(cmd)
        self._restore_cur_working_folder()
