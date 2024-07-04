# ========================================
# Import Python Modules (Standard Library)
# ========================================
import os
import re
import shutil

# =======
# Classes
# =======
class FoldersManagerCls:
    """
    This class creates the folder structure that the tool
    uses to perform the required analyses and to store
    the test results.
    NOTE: To facilitate access to specific folders within
    the created structure, this class includes a set of
    read-only attributes implemented with the property
    decorator.
    """
    # === Constructor ===
    def __init__(self, tool_name='cloudflow'):
        # Attribute initialization
        self.tool_name = tool_name
        # Call auxiliary methods
        self._set_default_values()

    # === Read-only Attribute ===
    @property
    def analysis_folder(self):
        return self._analysis_folder

    # === Read-only Attribute ===
    @property
    def log_files_folder(self):
        return self._log_files_folder

    # === Read-only Attribute ===
    @property
    def pysa_models_folder(self):
        return self._pysa_models_folder

    # === Read-only Attribute ===
    @property
    def pysa_results_folder(self):
        return self._pysa_results_folder

    # === Read-only Attribute ===
    @property
    def repo_full_path(self):
        return self._repo_full_path

    # === Read-only Attribute ===
    @property
    def report_files_folder(self):
        return self._report_files_folder

    # === Protected Method ===
    def _copy_orig_repo(self):
        """
        Method that copies all the files of the original
        repository into a dedicated folder with the
        analysis folder.
        """
        self._repo_full_path = os.path.join(self.analysis_folder, self.repo_name)
        shutil.copytree(self.orig_repo_full_path, self.repo_full_path)

    # === Protected Method ===
    def _create_analysis_folder(self):
        """
        Method that creates the analysis folder containing
        all the folders (i.e., top of the hierarchy) needed
        to analyse a repository.
        """
        print(f'--- All the analysis folders will be created in: {self.tool_repo_folder} ---')
        self._analysis_folder = os.path.join(self.tool_repo_folder,
                                             '-'.join([self.analysis_folder_id, self.repo_name]))
        os.mkdir(self.analysis_folder)

    # === Protected Method ===
    def _create_pysa_models_folder(self):
        """
        Method that creates the subfolder containing the Pysa models.
        """
        self._pysa_models_folder = os.path.join(self.analysis_folder, 'stubs', 'taint')
        os.makedirs(self.pysa_models_folder)

    # === Protected Method ===
    def _create_pysa_results_folder(self):
        """
        Method that creates the subfolder containing the Pysa results.
        """
        self._pysa_results_folder = os.path.join(self.analysis_folder, 'pysa-runs')
        os.mkdir(self._pysa_results_folder)

    # === Protected Method ===
    def _sanitize_orig_repo_full_path(self):
        """
        Method that sanitizes the string storing
        the original repository full path.
        """
        # Remove OS separator at the end of the string,
        # as this causes problems to other methods.
        self.orig_repo_full_path = re.sub(r'/$', '', self.orig_repo_full_path)

    # === Protected Method ===
    def _set_default_values(self):
        """
        Method that initializes all the required instance
        variables with their default values.
        """
        # The full path of the file where this module is
        # stored is used to obtain the full path of the
        # tool repository folder.
        module_full_path = os.path.realpath(__file__)
        self.tool_repo_folder = module_full_path.split(self.tool_name)[0]
        # The names of all the analysis folders begin with
        # the following id to facilitate their identification.
        self.analysis_folder_id = '-'.join([self.tool_name, 'analysis'])
        # Folder where all the report files are stored
        self.report_files_folder_id = '-'.join([self.tool_name, 'report-files'])
        # Folder where all the log files are stored
        self.log_files_folder_id = '-'.join([self.tool_name, 'log-files'])

    # === Method ===
    def create_folders_structure(self, orig_repo_full_path):
        """
        Method that creates the folder structure
        needed for the analysis of a repository.
        """
        # Attribute initialization
        self.orig_repo_full_path = orig_repo_full_path
        # Call auxiliary methods
        self._sanitize_orig_repo_full_path()
        # Name of the repository to be analysed (i.e., name
        # of the folder where all the files are stored).
        self.repo_name = os.path.basename(self.orig_repo_full_path)
        # Folder structure is created starting from top of hierarchy
        self._create_analysis_folder()
        # Create / fill subfolders within analysis folder
        self._copy_orig_repo()
        self._create_pysa_models_folder()
        self._create_pysa_results_folder()

    # === Method ===
    def create_log_files_folder(self):
        """
        Method that creates the folder where all the log
        files are stored.
        """
        self._log_files_folder = os.path.join(self.tool_repo_folder,
                                              self.log_files_folder_id)
        os.mkdir(self._log_files_folder)

    # === Method ===
    def create_report_files_folder(self):
        """
        Method that creates the folder where all the report
        files are stored.
        """
        self._report_files_folder = os.path.join(self.tool_repo_folder,
                                                 self.report_files_folder_id)
        os.mkdir(self._report_files_folder)

    # === Method ===
    def delete_all_created_folders(self):
        """
        Method that deletes all the created folders.
        """
        self.delete_analysis_folders()
        self.delete_log_files_folder()
        self.delete_report_files_folder()

    # === Method ===
    def delete_analysis_folders(self):
        """
        Method that deletes all the existing analysis folders.
        """
        for folder in (elem for elem in os.listdir(self.tool_repo_folder)
                       if elem.startswith(self.analysis_folder_id)):
            shutil.rmtree(os.path.join(self.tool_repo_folder, folder))

    # === Method ===
    def delete_log_files_folder(self):
        """
        Method that deletes the folder where all the log
        files are stored.
        """
        shutil.rmtree(os.path.join(self.tool_repo_folder, self.log_files_folder_id),
                      ignore_errors=True)

    # === Method ===
    def delete_report_files_folder(self):
        """
        Method that deletes the folder where all the report
        files are stored.
        """
        shutil.rmtree(os.path.join(self.tool_repo_folder, self.report_files_folder_id),
                      ignore_errors=True)
