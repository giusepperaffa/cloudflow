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
    def _extract_results_files_field_names(self):
        """
        Method that extracts the field names from a
        Pysa results file (CSV format), and returns
        them as list.
        """
        # Process analysis folders
        for analysis_folder in sorted(elem for elem in os.listdir(self.analysis_folders_full_path)
                                      if elem.startswith(self.analysis_folder_id)):
            # Process contents of the results folder
            results_folder_full_path = os.path.join(self.analysis_folders_full_path,
                                                    analysis_folder,
                                                    self.results_folder)
            # NOTE: The class assumes that all the Pysa results
            # files have the same structure. Therefore, when a
            # Pysa results file is successfully processed, the
            # cycle over the analysis folders is interrupted.
            if self.results_file in os.listdir(results_folder_full_path):
                try:
                    with open(os.path.join(results_folder_full_path, self.results_file),
                              mode='r') as csv_file_obj:
                        # Initialize CSV file reader
                        csv_reader = csv.DictReader(csv_file_obj)
                        # When no field name is extracted from the processed CSV
                        # file, an exception is raised, and a new results folder
                        # is processed.
                        if len(csv_reader.fieldnames) > 0:
                            return csv_reader.fieldnames
                        else:
                            raise ValueError
                except ValueError as e:
                    print('--- WARNING: No field name extracted from the following results file: ---')
                    print(f'--- {os.path.join(results_folder_full_path, self.results_file)} ---')

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
        # Data flows report file
        self.data_flows_report = 'cloudflow_data_flows_report.csv'

    # === Method ===
    def generate_data_flows_report(self):
        """
        Method that generates the data flows report.
        NOTE: The generation of the data flows report
        depends on the summary report. Therefore, the
        latter must already be available.
        """
        print('--- Data flows report being generated... ---')
        summary_report_full_path = os.path.join(self.report_files_folder,
                                                self.summary_report)
        data_flows_report_full_path = os.path.join(self.report_files_folder,
                                                   self.data_flows_report)
        # ----------------------
        # Preliminary processing
        # ----------------------
        # The CSV file generated by this method makes use
        # of field names included in the results files,
        # which are extracted with a dedicated method.
        fieldnames = ['Repository'] + self._extract_results_files_field_names()
        # --------------
        # Main algorithm
        # --------------
        with open(summary_report_full_path, mode='r') as summary_report_file_obj,\
            open(data_flows_report_full_path, mode='w') as data_flows_report_file_obj:
            # Initialize CSV file reader for summary report
            csv_reader = csv.DictReader(summary_report_file_obj)
            # Initialize CSV file writer for data flows report
            csv_writer = csv.DictWriter(data_flows_report_file_obj,
                                        fieldnames=fieldnames)
            csv_writer.writeheader()
            # Read summary report to identify repositories
            # where data flows have been detected.
            for summary_report_row in csv_reader:
                try:
                    if int(summary_report_row['Individual Data Flows']) > 0:
                        # Analysis folder of the target repository
                        target_analysis_folder = '-'.join([self.analysis_folder_id,
                                                           summary_report_row['Repository']])
                        # Full path of the target results folder
                        target_results_folder = os.path.join(self.analysis_folders_full_path,
                                                             target_analysis_folder,
                                                             self.results_folder)
                        with open(os.path.join(target_results_folder, self.results_file),
                                  mode='r') as target_file_obj:
                            # Initialize CSV file reader for target results file
                            target_results_file_reader = csv.DictReader(target_file_obj)
                            # Read target results file and write to data flows report
                            for row in target_results_file_reader:
                                data_flows_report_row = {'Repository': summary_report_row['Repository']}
                                data_flows_report_row.update(row)
                                csv_writer.writerow(data_flows_report_row)
                except:
                    print('--- WARNING: Individual data flows number not processed for repository: ---')
                    print(f"--- {summary_report_row['Repository']} ---")

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
                # Initialize line to be written in case of error
                # when processing the Pysa results.
                error_row = {'Repository': repo_id, 'Analysis': 'Error', 'Individual Data Flows': 'N/A'}
                # Process Pysa results 
                if self.successful_analysis_files & results_folder_files == self.successful_analysis_files:
                    try:
                        with open(os.path.join(results_folder_full_path,
                                               self.results_file), mode='r') as results_file_obj:
                            # Initialize CSV file reader
                            csv_reader = csv.DictReader(results_file_obj)
                            data_flows_number =  len([row['Issue'] for row in csv_reader])
                        # Add row to the summary report
                        csv_writer.writerow({'Repository': repo_id, 'Analysis': 'Completed', 'Individual Data Flows': data_flows_number})
                    except:
                        # Add row to the summary report
                        csv_writer.writerow(error_row)
                else:
                    # Add row to the summary report
                    csv_writer.writerow(error_row)
