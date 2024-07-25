# ========================================
# Import Python Modules (Standard Library)
# ========================================
import os
import traceback

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
from cloudflow.modules.postprocessingreslib import PostprocessingManagerCls
from cloudflow.modules.pluginprocessingreslib import PluginManagerCls
from cloudflow.modules.reportgenerationreslib import ReportManagerCls
from cloudflow.modules.logmanagementreslib import LogRedirectionManagerCls
from cloudflow.modules.toolconfigreslib import ToolConfigManagerCls

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
    def _get_plugin_info(self):
        """
        Method returning an instance of an object where all the
        plugin-related information is stored.
        """
        plugin_manager = PluginManagerCls(self.infrastruc_code_dict)
        return plugin_manager.plugin_extracted_info

    # === Protected Method ===
    def _prepare_analysis(self, repo_full_path):
        """
        Method that implements all the steps required prior
        to starting the actual analysis of the repository.
        """
        # Instantiate class that generates Pysa configuration file
        print('--- Pysa configuration file is about to be generated... ---')
        pysa_config_manager = PysaConfigManagerCls(self.folders_manager,
                                                   self.tool_config_manager)
        pysa_config_manager.generate_config_file()
        # Instantiate class that generates Pysa models
        print('--- Pysa models are about to be generated... ---')
        model_gen_manager = ModelGenerationManagerCls(self.handlers_dict,
                                                      self.infrastruc_code_dict,
                                                      self.infrastruc_code_file,
                                                      self.folders_manager,
                                                      self.perm_dict,
                                                      self.plugin_info,
                                                      self.tool_config_manager)
        model_gen_manager.generate_models()
        # Instantiate class that adds boto3-related type annotations
        print('--- Boto3-specific type annotations are being added... ---')
        type_ann_manager = TypeAnnotationManagerCls(repo_full_path)
        type_ann_manager.add_all_type_annotations()
        # Instantiate class that implements code synthesis and injection
        print('--- Synthesized code is being injected... ---')
        code_syn_inj_manager = CodeSynInjManagerCls(type_ann_manager.interf_objs_dict,
                                                    self.perm_dict,
                                                    self.perm_res_dict,
                                                    self.handlers_dict,
                                                    self.infrastruc_code_dict,
                                                    self.plugin_info)
        code_syn_inj_manager.inject_synthesized_code()
        # Instantiate class that handles the execution of Pysa
        print('--- Automated type inference is about to start... ---')
        self.pysa_exec_manager = PysaExecManagerCls(self.folders_manager)
        self.pysa_exec_manager.exec_type_inference()
        return

    # === Protected Method ===
    def _run_microbenchmarks_category(self, category):
        """
        Method that runs the category of microbenchmarks
        passed as input argument. The category is expected
        to be organized with a set of sub-folders that
        contain the repositories to be analysed.
        """
        for sub_folder in os.listdir(os.path.join(self.mb_suite_full_path,
                                                  category)):
                self.analyse_repos_within_folder(os.path.join(self.mb_suite_full_path,
                                                              category,
                                                              sub_folder))

    # === Method ===
    def analyse_microbenchmarks(self, mb_suite='cloudbench'):
        """
        Method that analyses the microbenchmarks suite
        specified as input parameter.
        """
        print('--- The following microbenchmarks suite is about to be tested: ---')
        self.mb_suite_full_path = os.path.join(self.folders_manager.tool_repo_folder,
                                               mb_suite)
        print(f'--- {self.mb_suite_full_path} ---')
        if self.config_obj.microbenchmarks in ('all', 'inter-procedural'):
            self._run_microbenchmarks_category('inter-procedural')
        if self.config_obj.microbenchmarks in ('all', 'intra-procedural'):
            self._run_microbenchmarks_category('intra-procedural')
        if self.config_obj.microbenchmarks in ('all', 'simple-apps'):
            self.analyse_repos_within_folder(os.path.join(self.mb_suite_full_path,
                                                          'simple-apps'))

    # === Method ===
    def analyse_repo(self, repo_full_path):
        """
        Method that implements the analysis pipeline designed
        for the CloudFlow tool. The code in this method is
        designed to analyse one repository only.
        """
        # Instantiate class that handles the configuration file used by the tool
        print('--- Tool configuration file is being processed... ---')
        self.tool_config_manager = ToolConfigManagerCls(self.config_obj.config_file)
        # Instantiate class that handles the folder structure used by the tool
        print('--- Folder structure is being created... ---')
        self.folders_manager.create_folders_structure(repo_full_path)
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
                # Extract plugin-related information
                self.plugin_info = self._get_plugin_info()
                # Perform steps required prior to starting analysis
                self._prepare_analysis(self.folders_manager.repo_full_path)
                print('--- Dataflow analysis is about to start... ---')
                self.pysa_exec_manager.exec_dataflow_analysis()
                print('--- Results postprocessing is about to start... ---')
                self.postproc_manager = PostprocessingManagerCls(self.folders_manager)
                self.postproc_manager.postprocess_pysa_results()
            except Exception as e:
                print('--- Exception raised - Details: ---')
                print(f'--- {e} ---')
                print()
                print('=============')
                print('| Traceback |')
                print('=============')
                print(traceback.format_exc())
                print('--- Analysis interrupted ---')
        else:
            print('--- Inconsistency detected - Analysis interrupted ---')

    # === Method ===
    def analyse_repos_within_folder(self, target_folder):
        """
        Methods that analyses all the repositories within
        the folder specified as input parameter.
        """
        try:
            for folder in sorted(item for item in os.listdir(target_folder)
                                 if os.path.isdir(os.path.join(target_folder, item))):
                print()
                print(f'=== Start analysis of repository: {folder} ===')
                self.analyse_repo(os.path.join(target_folder, folder))
        except FileNotFoundError as e:
            print('--- No analysis performed - Details: ---')
            print(f'--- {e} ---')

    # === Method ===
    def create_report_files(self):
        """
        Method that creates the report files within a
        dedicated folder.
        """
        print()
        self.report_manager = ReportManagerCls(self.folders_manager.tool_repo_folder,
                                               self.folders_manager.report_files_folder)
        self.report_manager.generate_summary_report()

    # === Method ===
    def perform_analysis(self):
        """
        Method that starts the analysis tool execution.
        """
        # Initialize folders manager object
        self.folders_manager = FoldersManagerCls()
        # Handle tool execution in log processing mode
        if self.config_obj.log_processing:
            print('--- CloudFlow log processing - Start ---')
            # The tool log processing relies on functionality
            # provided by the LogRedirectionManagerCls. Early
            # return avoids executing initialization steps
            # designed for other tool analysis modes.
            log_files_folder = os.path.join(self.folders_manager.tool_repo_folder,
                                            self.folders_manager.log_files_folder_id)
            self.log_redirection_manager = LogRedirectionManagerCls(log_files_folder)
            self.log_redirection_manager.split_log_file()
            return
        # Prepare execution by deleting all the created folders
        self.folders_manager.delete_all_created_folders()
        # Prepare execution by creating necessary folders
        self.folders_manager.create_log_files_folder()
        self.folders_manager.create_report_files_folder()
        # Initialize log redirection manager object and
        # activate stdout and stderr redirection.
        self.log_redirection_manager = LogRedirectionManagerCls(self.folders_manager.log_files_folder)
        self.log_redirection_manager.activate_log_redirection()
        print('--- CloudFlow analysis - Start ---')
        if self.config_obj.single:
            print('--- Analysis mode: Single repository ---')
            self.analyse_repo(self.config_obj.single)
        elif self.config_obj.multi:
            print('--- Analysis mode: Multiple repositories ---')
            self.analyse_repos_within_folder(self.config_obj.multi)
        elif self.config_obj.microbenchmarks:
            print('--- Analysis mode: Microbenchmarks suite ---')
            self.analyse_microbenchmarks()
        # Report generation
        self.create_report_files()
