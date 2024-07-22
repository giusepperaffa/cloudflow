# ========================================
# Import Python Modules (Standard Library)
# ========================================
from dataclasses import dataclass
import os

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.utils.fileprocessingreslib import extract_dict_from_yaml

# =======
# Classes
# =======
@dataclass(frozen=True)
class ToolConfigDefaultDataCls:
    """
    Data class that stores the default tool configuration values.
    NOTE: When a new parameter is added to the tool configuration
    file, this class needs to be updated to specify the default
    value of the new parameter.
    """
    package_mode: bool = False

class ToolConfigManagerCls:
    """
    Class that manages the extraction of information from the
    tool configuration file. The class exposes getters that
    should be used by the calling code to retrieve information
    from the tool configuration file.
    NOTE: When a new parameter is added to the tool configuration
    file, a dedicated getter method needs to be integrated into
    this class.
    """
    # === Constructor ===
    def __init__(self, tool_config_file):
        """
        Class constructor. Input arguments:
        -) tool_config_file: String specifying the configuration
        file as a string. If the file name is invalid, the class
        retuns default values for the configuration parameters. 
        """
        # Attribute initialization
        self.tool_config_file = tool_config_file
        self.tool_config_default = ToolConfigDefaultDataCls()
        # Read tool configuration file
        self._read_tool_config_file()

    # === Protected Method ===
    def _read_tool_config_file(self, config_folder='config'):
        """
        Method that maps the tool configuration file into
        a dictionary, which is made available as instance
        variable.
        """
        # Full path of the folder containing the configuration file
        config_folder_full_path = os.path.join(os.sep.join(__file__.split(os.sep)[:-2]), config_folder)
        # Process configuration file
        if self.tool_config_file is not None:
            self.tool_config_dict = extract_dict_from_yaml(config_folder_full_path,
                                                           self.tool_config_file)
        else:
            print('--- No configuration file specified - Default values will be used ---')

    # === Method ===
    def get_package_mode(self, repo_name):
        """
        Method that returns the package_mode configuration
        parameter for the repository specified as input
        argument (as a string). 
        """
        try:
            return eval(self.tool_config_dict[repo_name]['model-generation']['package-mode'])
        except:
            return self.tool_config_default.package_mode
