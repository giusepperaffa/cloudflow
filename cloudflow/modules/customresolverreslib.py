# ========================================
# Import Python Modules (Standard Library)
# ========================================
import re
import yaml

# =======
# Classes
# =======
class YAMLResolverCls:
    # ==== Constructor ===
    def __init__(self, yaml_file):
        """
        The full path of the YAML file has to be passed to the constructor.
        """
        self.yaml_file = yaml_file
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
        with open(self.yaml_file, mode='r') as file_obj:
            self.ref_dict = yaml.load(file_obj, Loader=yaml.BaseLoader)

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
        # Regular expression used to identify values specified via external files
        file_detect_reg_exp = re.compile(r'^file\(.*\)')
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
                for key in re.sub('^\$?\{?self:', '', extracted_str).split('.'):
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
                if file_detect_reg_exp.search(extracted_str) is not None:
                    return extracted_str
                else:
                    return value
        else:
            return value

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
