# ========================================
# Import Python Modules (Standard Library)
# ========================================
import os
import re
import yaml

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.utils.fileprocessingreslib import extract_dict_from_yaml, extract_dict_from_json

# ==========================
# Module Regular Expressions
# ==========================
# Regular expression used to identify external files
ext_file_reg_exp = re.compile(r'\{file\((?P<file_path>.+)\)\}')
# Regular expression used to identify values specified via external files
ext_file_value_reg_exp = re.compile(r'\{file\((?P<file_path>.+)\):(?P<config_param>.+)\}')

# =========
# Functions
# =========
def resolve_value_from_yaml(unres_value, config_dict, max_recursion=10):
    """
    Function that recursively attempts to resolve a value
    (specified as a string) from the YAML file by using
    the dictionary that maps this configuration file. The
    parameter max_recursion controls the maximum number
    of allowed recursive calls.
    NOTE: This function aims at resolving individual strings,
    and can be used, for instance, to attempt to resolve
    specific information included in the YAML that the main
    resolver used by the tool has not managed to resolve.
    """
    # Regular expression that identifies unresolved strings
    # according to the Serverless Framework syntax.
    unres_val_reg_exp = re.compile(r'\$\{self:([\w\.\-]+?)\}')
    if (unres_val_reg_exp.search(unres_value) is not None) and (max_recursion != 0):
        print('--- Attempting to resolve information from YAML file... ---')
        # Process all the substrings to be resolved.
        for substring in unres_val_reg_exp.findall(unres_value):
            # Extracted substrings normally include '.' to separate
            # the different fields, but '.' cannot be used with the
            # configuration dictionary. The substring is processed
            # to ensure that the resolved value is retrieved from
            # the dictionary by using standard dictionary syntax.
            try:
                for depth, key in enumerate(substring.split('.')):
                    if depth == 0:
                        res_value = config_dict[key]
                    else:
                        res_value = res_value[key]
                # Substitute specific substring with the resolved value
                unres_value = re.sub(r'\$\{self:' + substring + r'\}', res_value, unres_value)
            except KeyError as e:
                print('--- Exception raised - The following dictionary key was not found: ---')
                print(f'--- {e} ---')
            except Exception as e:
                print('--- Exception raised - Details: ---')
                print(f'--- {e} ---')
        # Recursive call.
        return resolve_value_from_yaml(unres_value, config_dict, max_recursion - 1)
    else:
        # Return input argument, because modified in place.
        return unres_value

def check_if_resolved(input):
    """
    Function that checks the input argument and returns
    True if it is fully resolved, False otherwise. The
    input argument can be either:
    -) A string.
    -) An iterable. If so, the function returns True
    only if ALL the strings are resolved.
    If an exception is raised, the function returns False.
    """
    # Regular expression that detects unresolved strings
    unres_detect_reg_exp = re.compile(r'\$\{')
    try:
        if isinstance(input, str):
            return unres_detect_reg_exp.search(input) is None
        else:
            return all((unres_detect_reg_exp.search(elem) is None) for elem in input)
    except Exception as e:
        print(f'--- Exception raised while checking if the following input is resolved: ---')
        print(f'--- {input} ---')
        print('--- Details: ---')
        print(f'--- {e} ---')
        return False

# =======
# Classes
# =======
class ExtFilesManagerCls:
    """
    Class providing the functionality needed to extract
    information specified in the YAML file via external
    file (i.e., referenced in the YAML file).
    """
    # === Constructor ===
    def __init__(self, yaml_file, ref_dict=None):
        """
        Class constructor. Input parameters:
        -) yaml_file: YAML file full path.
        -) ref_dict: Reference dictionary. By default,
        the dictionary that maps the YAML is used as
        a reference during the resolution process.
        However, a dictionary with partially resolved
        values can be passed to increase the chances
        of a successful resolution.
        """
        self.yaml_file = yaml_file
        self.init_ref_dict(ref_dict)

    # === Protected Method ===
    def _get_ext_file_full_path(self, rel_path):
        """
        Method that returns the full path corresponding
        to the relative path passed as input argument.
        The latter is assumed to be a path relative to
        the YAML file.
        """
        # Full path of folder containing YAML file
        yaml_file_folder = os.path.dirname(self.yaml_file)
        # Regular expression - Detect same folder as YAML file
        same_folder_reg_exp = re.compile(r'^\./')
        # Regular expression - Detect folder one level up (compared to YAML file)
        one_level_up_reg_exp = re.compile(r'^\.\./')
        # Obtain full path
        if same_folder_reg_exp.search(rel_path) is not None:
            return os.path.join(yaml_file_folder,
                                same_folder_reg_exp.sub('', rel_path))
        elif one_level_up_reg_exp.search(rel_path) is not None:
            return os.path.join(os.sep.join(yaml_file_folder.split(os.sep)[:-1]),
                                one_level_up_reg_exp.sub('', rel_path))
        else:
            return os.path.join(yaml_file_folder, rel_path)

    # === Protected Method ===
    def _get_serialized_file(self, yaml_file_full_path):
        """
        Method used to serialize the YAML file specified as input.
        """
        return yaml.serialize(yaml.compose(open(yaml_file_full_path, mode='r'),
                                           Loader=yaml.BaseLoader))

    # === Protected Method ===
    def _process_nested_dict_key(self, input_dict, input_key):
        """
        Method that returns a value stored in a nested dictionary
        (i.e., a dictionary containing other dictionaries) by
        processing a key specified with dot notation. Example:
        if input_key is a.b, the returned value will be:
        input_dict[a][b]. Input arguments:
        -) input_dict: Input dictionary
        -) input_key: String specifying key with dot notation
        """
        for depth, key in enumerate(input_key.split('.')):
            if depth == 0:
                extracted_value = input_dict[key]
            else:
                extracted_value = extracted_value[key]
        return extracted_value

    # === Protected Method ===
    def _process_format(self, yaml_file_full_path, offset):
        """
        Method that processes the input YAML file by adding an
        a number of whitespace characters equal to the offset,
        which must be specified as integer. The YAML file is
        serialized, modified, and returned in serialized form.
        NOTE: The offset is added to all the lines of the YAML
        file, except for the first.
        """
        serialized_file = self._get_serialized_file(yaml_file_full_path)
        # Separate the first line of the serialized file from
        # the rest, which has to be further processed.
        serialized_file_first, serialized_file_to_proc = serialized_file.split('\n', 1)
        serialized_file_with_offset = [(' ' * offset) + elem
                                       for elem in serialized_file_to_proc.split('\n')]
        return '\n'.join([serialized_file_first] + serialized_file_with_offset)

    # === Protected Method ===
    def _tokenize(self):
        """
        Method used to identify within the YAML file the tokens
        with values specifying external files. It is implemented
        as a generator that yields the start and the end of the
        token, along with the extracted external file path.
        """
        serialized_file = self._get_serialized_file(self.yaml_file)
        for token in yaml.scan(serialized_file, Loader=yaml.BaseLoader):
            if isinstance(token, yaml.ScalarToken) and (ext_file_reg_exp.search(token.value) is not None):
                yielded_tuple = (token.start_mark,
                                 token.end_mark,
                                 ext_file_reg_exp.search(token.value).group('file_path'))
                yield yielded_tuple

    # === Method ===
    def init_ref_dict(self, ref_dict):
        """
        Method used to initialize the reference dictionary.
        """
        if ref_dict is not None:
            self.ref_dict = ref_dict
        else:
            self.ref_dict = extract_dict_from_yaml(os.path.dirname(self.yaml_file),
                                                   os.path.basename(self.yaml_file))

    # === Method ===
    def resolve_ext_files(self):
        """
        Method that identifies external files within the YAML file and
        attempts to resolve them, i.e., include their contents within
        the YAML file. The updated YAML file is loaded at the end of
        the processing, and the corresponding updated dictionary is
        returned.
        """
        serialized_file = self._get_serialized_file(self.yaml_file)
        # Code developed by using this example on how to tokenize a YAML document:
        # https://realpython.com/python-yaml/#tokenize-a-yaml-document
        for start, end, ext_file_path in reversed(list(self._tokenize())):
            try:
                print(f'--- Attempting to resolve external file: {ext_file_path} ---')
                # Resolve external file path
                res_ext_file_path = resolve_value_from_yaml(ext_file_path, self.ref_dict)
                # External files are typically specified in the YAML with
                # relative paths. A dedicated method extracts the full
                # path to facilitate further processing.
                ext_file_path_full_path = self._get_ext_file_full_path(res_ext_file_path)
                # Process identified external file
                serialized_file_to_add = self._process_format(ext_file_path_full_path, start.column)
                serialized_file = serialized_file[:start.index] + \
                    serialized_file_to_add + serialized_file[end.index:]
            except Exception as e:
                print(f'--- External file {ext_file_path} could not be resolved ---')
                print('--- Details: ---')
                print(f'--- {e} ---')
        # Return the dictionary mapping the modified YAML file
        return yaml.load(serialized_file, Loader=yaml.BaseLoader)

    # === Method ===
    def resolve_value_from_ext_file(self, unres_val):
        """
        Method that attempts to resolve a value specified in the processed
        YAML file via an external file (YAML or JSON format). For instance:
        -) ${file(core/iam.yml):iamRoleStatements}
        The method returns the resolved value as a string.
        Input parameter:
        -) unres_val: Unresolved value (string)
        NOTE: If the passed unresolved value is not specified through an
        external file or another exception is raised, the input argument
        is returned unaltered.
        """
        # Initialize dictionary with functions used to process
        # the external file. Functions are different depending
        # upon the external file extension.
        proc_func_dict = dict()
        proc_func_dict['.json'] = extract_dict_from_json
        proc_func_dict['.yml'] = extract_dict_from_yaml
        proc_func_dict['.yaml'] = extract_dict_from_yaml
        # Process unresolved value
        try:
            print(f'--- Attempting to resolve value {unres_val} from external file... ---')
            # Extract and resolve external file path
            ext_file_path = ext_file_value_reg_exp.search(unres_val).group('file_path')
            res_ext_file_path = resolve_value_from_yaml(ext_file_path, self.ref_dict)
            # External files are typically specified in the YAML with
            # relative paths. A dedicated method extracts the full
            # path to facilitate further processing.
            ext_file_path_full_path = self._get_ext_file_full_path(res_ext_file_path)
            # Obtain external file dictionary
            ext_file_extension = os.path.splitext(res_ext_file_path)[-1]
            ext_file_dict = proc_func_dict[ext_file_extension](os.path.dirname(ext_file_path_full_path),
                                                               os.path.basename(ext_file_path_full_path))
            # Extract and resolve external file dictionary key that identifies the value
            ext_file_key = ext_file_value_reg_exp.search(unres_val).group('config_param')
            res_ext_file_key = resolve_value_from_yaml(ext_file_key, self.ref_dict)
            # Return identified value as a string
            return str(self._process_nested_dict_key(ext_file_dict, res_ext_file_key))
        except Exception as e:
            print(f'--- Value {unres_val} could not be resolved ---')
            print('--- Details: ---')
            print(f'--- {e} ---')
            return unres_val

class YAMLResolverCls:
    # ==== Constructor ===
    def __init__(self, yaml_file, resolve_ext_files_enable=False):
        """
        Class constructor. Input arguments:
        -) yaml_file: Full path of the YAML file to be resolved.
        -) resolve_ext_files_enable: Boolean argument that enables
        (True) / disables (False) the resolution of external files
        referenced in the YAML. Disabling their resolution can be
        helpful for testing purposes.
        """
        self.yaml_file = yaml_file
        self._resolve_ext_files(resolve_ext_files_enable)
        self.init_ref_dict()

    # === Method ===
    def get_root(self):
        """
        Method that maps the unresolved YAML file onto an in-memory data
        structure that can be easily traversed and modified.
        """
        # More information about the yaml.compose function avalable at:
        # https://realpython.com/python-yaml/
        with open(self.yaml_file, mode='r') as file_obj:
            self.root = yaml.compose(file_obj, yaml.BaseLoader)

    # === Method ===
    def init_ref_dict(self):
        """
        Method that maps the unresolved YAML file onto a reference dictionary.
        """
        self.ref_dict = extract_dict_from_yaml(os.path.dirname(self.yaml_file),
                                               os.path.basename(self.yaml_file))

    # === Method ===
    def _process_value(self, value):
        """
        Method that recursively processes a value extracted from the YAML file
        to resolve it. If a value is specified via an external file, the code
        attempts to resolve the file path only, but it does not process the
        file (if needed, this can be done by the calling code).
        """
        # Regular expression used to identify unresolved values
        unres_val_reg_exp = re.compile(r'\$\{(.*)\}')
        search_obj = unres_val_reg_exp.search(value)
        if search_obj is not None:
            extracted_str = search_obj.group(1)
            try:
                # This control statement deals with the Serverless Framework
                # syntax that allows specifying a value and a fallback value.
                # The latter is the one processed, because when this syntax
                # is used, the value is normally taken from the cli. Processing
                # of options passed via cli is currently not supported. Info at:
                # https://www.serverless.com/framework/docs/guides/parameters
                if ',' in extracted_str:
                    extracted_str = extracted_str.split(',')[1].strip()
                    if re.search('^(self:|opt:|env:)', extracted_str) is None:
                        # The extracted string is detected as fully resolved.
                        return extracted_str
                # The following code handles the case where the extracted string
                # contains in turn an unresolved part. A recursive call is used
                # to fully resolve the extracted string.
                nested_search_obj = unres_val_reg_exp.search(extracted_str)
                if nested_search_obj is not None:
                    extracted_str = extracted_str[:nested_search_obj.start()] + \
                    self._process_value('${' + nested_search_obj.group(1) + '}') + \
                    extracted_str[nested_search_obj.end():]
                # The following code assumes that there are no other occurrences
                # of ${...} within the extracted string.
                res_value = self.ref_dict
                # This cycle is needed because the unresolved value is specified
                # by using '.' notation, but this cannot be used to traverse
                # self.ref_dict, which is a standard dictionary.
                for key in re.sub(r'^\$?\{?self:', '', extracted_str).split('.'):
                    # The dictionary method get is not used in the following
                    # code, as extracting None when a dictionary key is invalid
                    # breaks the yaml module parser.
                    try:
                        res_value = res_value[key]
                    except KeyError:
                        raise ValueError
                return self._process_value(value[:search_obj.start()]) + \
                    res_value + self._process_value(value[search_obj.end():])
            except Exception as e:
                print(f'--- Value {extracted_str} could not be resolved ---')
                if ext_file_value_reg_exp.search('{' + extracted_str + '}') is not None:
                    # Initialize external files manager
                    ext_files_manager = ExtFilesManagerCls(self.yaml_file, self.ref_dict)
                    return ext_files_manager.resolve_value_from_ext_file('{' + extracted_str + '}')
                else:
                    return value
        else:
            return value

    # === Method ===
    def _resolve_ext_files(self, enable=True):
        """
        Method that resolves external files referenced in the YAML,
        if the Boolean input parameter is set to True (otherwise,
        no processing takes place). As a result of the resolution,
        the YAML file passed to the constructor is modified by this
        method.
        """
        if enable:
            # Create instance of class that manages external files
            ext_files_manager = ExtFilesManagerCls(self.yaml_file)
            extracted_dict = ext_files_manager.resolve_ext_files()
            with open(self.yaml_file, mode='w') as file_obj:
                yaml.dump(extracted_dict, file_obj)

    # === Method ===
    def resolve_yaml(self, output='dict'):
        """
        Method that returns the resolved YAML file. The input parameter
        output (string) determines the type of the returned object (two
        values only supported: 'dict' and 'str').
        """
        self.get_root()
        self._visit(self.root)
        if output == 'dict':
            return yaml.load(yaml.serialize(self.root), Loader=yaml.BaseLoader)
        elif output == 'str':
            return yaml.serialize(self.root)
        else:
            raise ValueError('--- Unrecognized output type ---')

    # === Method ===
    def _visit(self, node):
        """
        Method used to recursively visit the in-memory data structure mapping
        the YAML file being processed. Traversed value nodes are processed by
        calling a dedicated method of the class.
        """
        # Code developed starting from example avalable at:
        # https://realpython.com/python-yaml/
        if isinstance(node, yaml.ScalarNode):
            node.value = self._process_value(node.value)
            # Reference dictionary update. It is necessary to ensure that it
            # contains all the resolved values, as the successful resolution
            # of some values might depend upon the resolution of others.
            self.ref_dict = yaml.load(yaml.serialize(self.root), Loader=yaml.BaseLoader)
            return node.value
        elif isinstance(node, yaml.SequenceNode):
            return [self._visit(child) for child in node.value]
        elif isinstance(node, yaml.MappingNode):
            return {self._visit(key): self._visit(value) for key, value in node.value}
