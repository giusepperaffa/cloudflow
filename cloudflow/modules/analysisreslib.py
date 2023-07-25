# ========================================
# Import Python Modules (Standard Library)
# ========================================
import os

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.modules.customresolverreslib import YAMLResolverCls
from cloudflow.modules.handlerseventsreslib import HandlersEventsIdentifierCls
from cloudflow.modules.permissionsreslib import PermissionsIdentifierCls
from cloudflow.modules.typeannotationreslib import TypeAnnotationManagerCls
from cloudflow.modules.codesyninjreslib import CodeSynInjManagerCls
from cloudflow.modules.foldersmanagementreslib import FoldersManagerCls
from cloudflow.modules.modelgenerationreslib import ModelGenerationManagerCls
from cloudflow.modules.pysaconfigexecreslib import PysaConfigManagerCls, PysaExecManagerCls

# =========
# Functions
# =========
def find_infrastruc_code_file(repo_full_path):
    """
    Function returning the full path of the YAML infrastructure
    code file as a string. When the repository contains multiple
    infrastructure code files, the first identified by the standard
    library function os.walk is returned.
    NOTE: The function returns None in these cases:
    1) The repository folder does not exist.
    2) No infrastructure code file is found.
    """
    if os.path.isdir(repo_full_path):
        for root, dirs, files in os.walk(repo_full_path):
            print('--- Searching for infrastructure code file... ---')
            for flt_file in (file for file in files if file in
                            ('serverless.yml', 'serverless.yaml')):
                print('--- Found infrastructure code file: ---')
                print(f'--- {os.path.join(root, flt_file)} ---')
                return os.path.join(root, flt_file)
            else:
                print('--- No infrastructure code file found! ---')
                return
    else:
        print('--- The specified repository does not exist! ---')
        return

# =======
# Classes
# =======
class AnalysisManagerCls:
    # === Constructor ===
    def __init__(self, config_obj):
        self.config_obj = config_obj

    # === Protected Method ===
    def _get_handlers_dict(self):
        """
        Method returning the handlers dictionary, which is
        obtained by using a dedicated resource included in
        another module of the package.
        """
        # Instantiate class extracting handlers and events-related information
        he_identifier = HandlersEventsIdentifierCls(self.infrastruc_code_dict)
        he_identifier.pretty_print_handlers_dict()
        return he_identifier.handlers_dict

    # === Protected Method ===
    def _get_infrastruc_code_dict(self):
        """
        Method that maps the infrastructure code file into
        a dictionary. The code relies on the custom resolver
        included in the package.
        """
        # Instantiate custom resolver class
        yaml_resolver = YAMLResolverCls(self.infrastruc_code_file)
        return yaml_resolver.resolve_yaml()

    # === Protected Method ===
    def _get_permissions_dicts(self):
        """
        Method returning the dictionaries that store information
        about permissions. The code relies on a dedicated resource
        in another module of the package.
        """
        #  Instantiate class extracting permissions-related information
        perm_identifier = PermissionsIdentifierCls(self.infrastruc_code_dict)
        perm_identifier.pretty_print_perm_dict()
        perm_identifier.pretty_print_resources()
        return perm_identifier.perm_dict, perm_identifier.perm_res_dict

    # === Protected Method ===
    def _prepare_analysis(self, repo_full_path):
        """
        Method that implements all the steps required prior
        to starting the actual analysis of the repository.
        """
        # Instantiate class that generates Pysa configuration file
        print('--- Pysa configuration file is about to be generated... ---')
        pysa_config_manager = PysaConfigManagerCls(self.folders_manager)
        pysa_config_manager.generate_config_file()
        # Instantiate class that generates Pysa models
        print('--- Pysa models are about to be generated... ---')
        model_gen_manager = ModelGenerationManagerCls(self.handlers_dict,
                                                      self.infrastruc_code_dict,
                                                      self.infrastruc_code_file,
                                                      self.folders_manager.pysa_models_folder)
        model_gen_manager.generate_models()
        # Instantiate class that adds boto3-related type annotations
        print('--- Boto3-specific type annotations are being added... ---')
        type_ann_manager = TypeAnnotationManagerCls(repo_full_path)
        type_ann_manager.add_all_type_annotations()
        # Instantiate class that implements code synthesis and injection
        print('--- Synthesized code is being injected... ---')
        code_syn_inj_manager = CodeSynInjManagerCls(type_ann_manager.interf_objs_dict,
                                                    self.perm_dict,
                                                    self.handlers_dict,
                                                    self.infrastruc_code_dict)
        code_syn_inj_manager.inject_synthesized_code()
        # Instantiate class that handles the execution of Pysa
        print('--- Automated type inference is about to start... ---')
        self.pysa_exec_manager = PysaExecManagerCls(self.folders_manager)
        self.pysa_exec_manager.exec_type_inference()
        return

    # === Method ===
    def analyse_repo(self, repo_full_path):
        """
        Method that implements the analysis pipeline designed
        for the CloudFlow tool. The code in this method is
        designed to analyse one repository only.
        """
        # Instantiate class that handles the folder structure used by the tool
        print('--- Folder structure is being created... ---')
        self.folders_manager = FoldersManagerCls(repo_full_path)
        self.folders_manager.create_folders_structure()
        # Infrastructure code identification
        self.infrastruc_code_file = find_infrastruc_code_file(self.folders_manager.repo_full_path)
        if self.infrastruc_code_file:
            try:
                # Map infrastructure code file into a dictionary
                self.infrastruc_code_dict = self._get_infrastruc_code_dict()
                # Extract handlers and events-related information
                self.handlers_dict = self._get_handlers_dict()
                # Extract permissions-related information
                self.perm_dict, self.perm_res_dict = self._get_permissions_dicts()
                # Perform steps required prior to starting analysis
                self._prepare_analysis(self.folders_manager.repo_full_path)
                print('--- Dataflow analysis is about to start... ---')
                self.pysa_exec_manager.exec_dataflow_analysis()
            except Exception as e:
                print('--- Exception raised - Details: ---')
                print(f'--- {e} ---')
                print('--- Analysis interrupted ---')
        else:
            print('--- Inconsistency detected - Analysis interrupted ---')

    # === Method ===
    def perform_analysis(self):
        print('--- CloudFlow analysis - Start ---')
        if self.config_obj.single:
            print('--- Analysis mode: Single repository ---')
            self.analyse_repo(self.config_obj.single)
        elif self.config_obj.multi:
            print('--- Analysis mode: Multiple repositories ---')
            for folder in (item for item in os.listdir(self.config_obj.multi) if
                           os.path.isdir(os.path.join(self.config_obj.multi, item))):
                print()
                print(f'=== Start analysis of repository: {folder} ===')
                self.analyse_repo(os.path.join(self.config_obj.multi, folder))
