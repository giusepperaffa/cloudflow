# ========================================
# Import Python Modules (Standard Library)
# ========================================
import csv
import os
import re

# =======
# Classes
# =======
class ReportManagerCls:
    # === Constructor ===
    def __init__(self,
                 analysis_folders_full_path,
                 report_files_folder):
        """
        Class constructor. Input arguments:
        -) analysis_folders_full_path: String specifying the
        folder with all the tool analysis folders (full path).
        -) report_files_folder: String specifying the folder
        where all the report files will be stored (full path).
        """
        # Attribute initialization
        self.analysis_folders_full_path = analysis_folders_full_path
        self.report_files_folder = report_files_folder
        # Call auxiliary methods
        self._set_default_values()

    # === Protected Method ===
    def _set_default_values(self):
        """
        Method that initializes all the required instance
        variables with their default values.
        """
        # Folder within an analysis folder where results are stored.
        self.results_folder = 'pysa-runs'
        # File within the results folder with Pysa results  
        self.results_file = 'pysa_results.csv'
        # String identifying tool analysis folders. These must begin
        # with this string.
        self.analysis_folder_id = 'cloudflow-analysis'
        # Regular expression used to extract the analysed repository
        # name from the CloudFlow analysis folder.
        self.repo_id_reg_exp = re.compile(r'^' + self.analysis_folder_id + r'-')
        # Successful analysis files. Both files must be found within
        # the results folder for the analysis to be considered successful.
        self.successful_analysis_files = set(['taint-metadata.json',
                                              'taint-output.json'])
        # Summary report file
        self.summary_report = 'cloudflow_summary_report.csv'
        # Summary report fieldnames
        self.summary_report_fieldnames = ['Repository',
                                          'Analysis',
                                          'Individual Data Flows']

    # === Method ===
    def generate_summary_report(self):
        """
        Method that generates the summary report.
        """
        print('--- Summary report being generated... ---')
        summary_report_full_path = os.path.join(self.report_files_folder,
                                                self.summary_report)
        # Create CSV file with summary_report
        with open(summary_report_full_path, mode='w') as summary_report_file_obj:
            # Initialize CSV file writer
            csv_writer = csv.DictWriter(summary_report_file_obj,
                                        fieldnames=self.summary_report_fieldnames)
            csv_writer.writeheader()
            # Process all analysis folders
            for analysis_folder in sorted(elem for elem in os.listdir(self.analysis_folders_full_path)
                                          if elem.startswith(self.analysis_folder_id)):
                # Process contents of the results folder
                results_folder_full_path = os.path.join(self.analysis_folders_full_path,
                                                        analysis_folder,
                                                        self.results_folder)
                results_folder_files = set(os.listdir(results_folder_full_path))
                # Extract analysed repository name
                repo_id = self.repo_id_reg_exp.sub('', analysis_folder)
                # Process Pysa results 
                if self.successful_analysis_files & results_folder_files == self.successful_analysis_files:
                    with open(os.path.join(results_folder_full_path,
                                           self.results_file), mode='r') as results_file_obj:
                        # Initialize CSV file reader
                        csv_reader = csv.DictReader(results_file_obj)
                        data_flows_number =  len([row['Issue'] for row in csv_reader])
                    # Add row to the summary report
                    csv_writer.writerow({'Repository': repo_id, 'Analysis': 'Completed', 'Individual Data Flows': data_flows_number})
                else:
                    # Add row to the summary report
                    csv_writer.writerow({'Repository': repo_id, 'Analysis': 'Error', 'Individual Data Flows': 'N/A'})
