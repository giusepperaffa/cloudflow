# ========================================
# Import Python Modules (Standard Library)
# ========================================
import json
import os

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
    def __init__(self, folders_manager, virtual_env='experiments'):
        """
        Class constructor. Input arguments:
        -) folders_manager: Instance of folders manager
        object created with the tool's dedicated module
        -) virtual_env: String specifying the name of
        the virtual environment where Pysa is installed.
        Default value: 'experiments'.
        """
        # Attribute initialization
        self.folders_manager = folders_manager
        self.virtual_env = virtual_env
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
        