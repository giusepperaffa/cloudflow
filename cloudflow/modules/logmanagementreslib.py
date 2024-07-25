# ========================================
# Import Python Modules (Standard Library)
# ========================================
import logging
import os
import re
import sys

# =======
# Classes
# =======
class LogRedirectionManagerCls:
    # === Constructor ===
    def __init__(self,
                 log_files_folder):
        """
        Class constructor. Input arguments:
        -) log_files_folder: String specifying the folder
        with all the tool log files (full path).
        """
        # Attribute initialization
        self.log_files_folder = log_files_folder
        # Call auxiliary methods
        self._set_default_values()

    # === Protected Method ===
    def _create_repo_log_file(self, repo, repo_log_file_lines):
        """
        Method that creates repository-specific log files.
        Input arguments:
        -) repo: String specifying the repository name.
        -) repo_log_file_lines: List containing all the
        lines to be written to the repository-specific
        log file.
        """
        # Initialize basename for repository-specific log file
        repo_log_file_basename = re.sub(r'_file$',
                                        '_repo',
                                        os.path.splitext(self.log_file_name)[0])
        repo_log_file_full_path = os.path.join(self.log_files_folder,
                                               '_'.join([repo_log_file_basename, repo + '.log']))
        with open(repo_log_file_full_path, mode='w') as repo_log_file_obj:
            repo_log_file_obj.writelines(repo_log_file_lines)

    # === Protected Method ===
    def _set_default_values(self):
        """
        Method that initializes all the required instance
        variables with their default values.
        """
        # Name of the log file generated during the tool
        # execution. This log file contains information
        # about all the analysed repositories.
        self.log_file_name = 'cloudflow_log_file.log'
        self.log_file_full_path = os.path.join(self.log_files_folder, self.log_file_name)
        # Regular expression used to identify where the
        # log entries for a specific repository start.
        self.repo_log_start_reg_exp = re.compile('^=== Start analysis of repository: (?P<repo>[\w\-\.]+) ===')

    # === Protected Method ===
    def _set_log_redirection(self, *args, **kwargs):
        """
        Method that sets up the redirection of both stdout
        and stderr.
        NOTE: The redirection is set up in such a way that
        both streams are printed on the console as well.
        See documentation of the class StreamToLogger for
        additional information.
        """
        logging.basicConfig(*args, **kwargs)
        # Stdout redirection set-up
        stdout_logger = logging.getLogger('STDOUT')
        sl = StreamToLogger(stdout_logger, sys.stdout, logging.INFO)
        sys.stdout = sl
        # Stderr redirection set-up
        stderr_logger = logging.getLogger('STDERR')
        sl = StreamToLogger(stderr_logger, sys.stderr, logging.ERROR)
        sys.stderr = sl

    # === Method ===
    def activate_log_redirection(self):
        """
        Method that activates the redirection of both stdout
        and stderr.
        NOTE: See documentation of the class StreamToLogger
        for additional information.
        """
        self._set_log_redirection(level=logging.DEBUG,
                                  format="%(message)s",
                                  filename=self.log_file_full_path,
                                  filemode='w')

    # === Method ===
    def split_log_file(self):
        """
        Method that creates repository-specific log files
        by splitting the tool log file.
        """
        with open(self.log_file_full_path, mode='r') as log_file_obj:
            # Flag that enables copying to a repository-specific log file
            copy_enable = False
            # Auxiliary variable to track processed repositories
            repo = None
            # Process log file to be split 
            for line in log_file_obj:
                if self.repo_log_start_reg_exp.search(line) is not None:
                    previous_repo = repo
                    repo = self.repo_log_start_reg_exp.search(line).group('repo')
                    print(f"--- Start of log file for repository {repo} detected... ---")
                    # Enable copying to repository-specific log file
                    copy_enable = True
                    # Write to previous repository-specific log file
                    try:
                        self._create_repo_log_file(previous_repo, repo_log_file_lines)
                    except Exception as e:
                        pass
                    # Store first line of next repository-specific log file
                    repo_log_file_lines = [line]
                elif copy_enable:
                    # Store line of the repository-specific log file
                    repo_log_file_lines.append(line)
            else:
                try:
                    # Create last repository-specific log file at the end of
                    # the for cycle. If the previous cycle does not find the
                    # start of the log file for any repository, the following
                    # statement raises an exception.
                    self._create_repo_log_file(repo, repo_log_file_lines)
                except:
                    # No recovery action required
                    pass

class StreamToLogger:
    """
    Fake file-like stream object that redirects writes
    to a logger instance.
    CREDITS: This class was developed by using the code
    and explanations provided by:
    -) Ferry Boender - Website:
    https://www.electricmonk.nl/log/2011/08/14/redirect-stdout-and-stderr-to-a-logger-in-python/
    -) Karthikeyan Natarajan - Website:
    https://karthikeyann.github.io/blog/logging-stdout-stderr-to-file/
    """
    # === Constructor ===
    def __init__(self, logger, stream=sys.stdout, log_level=logging.INFO):
        self.logger = logger
        self.stream = stream
        self.log_level = log_level
        self.linebuf = ''

    # === Method ===
    def write(self, buf):
        self.stream.write(buf)
        self.linebuf += buf

    # === Method ===
    def flush(self):
        # Flush all handlers
        for line in self.linebuf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())
        self.linebuf = ''
        self.stream.flush()
        for handler in self.logger.handlers:
            handler.flush()
