# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast

# ========================================
# Import Python Modules (Project-specific)
# ========================================
from cloudflow.utils.astprocessingreslib import get_call_input_ast_node

# =========
# Functions
# =========
def analyse_event_filtering(service_name,
                            event_filtering_info,
                            api_call_ast_node,
                            infrastruc_code_dict,
                            handler_name,
                            sc_file):
    """
    Function that determines whether an API call is subject to
    event filtering by comparing the event filtering-related
    information with the event filtering-relevant API input
    arguments. The function returns a Boolean, i.e., True =>
    Filtering successful (i.e., API call allowed), False =>
    Filtering unsuccessful (i.e., API call not allowed).
    NOTE: To minimize false negatives, the function assumes
    that the filtering is successful when there is not enough
    information to establish otherwise. Therefore, it should
    be used with the analysis code that assesses the permissions.
    The following input arguments are analysed:
    -) service_name: Input specifying as a string the name of
    the relevant cloud service.
    -) event_filtering_info: Data structure with the information
    that allows identifying the event filtering-relevant API input
    arguments. With the adopted structure of the API configuration
    file, this input is a list of dictionaries, where each of them
    is dedicated to a specific input argument. Both keys and
    values are expected to be strings. NOTE: if the API does
    not have any event filtering-relevant input arguments, None
    should be passed instead.
    -) api_call_ast_node: AST node of the API call.
    -) infrastruc_code_dict: Dictionary that maps the YAML file
    for the application under test.
    -) handler_name: Input specifying as a string the name of
    the relevant handler.
    -) sc_file: Source code file to be processed (full path).
    """
    # ==================
    # Preliminary checks
    # ==================
    # Preliminary checks are implemented to identify specific cases
    # when the function can exit without running the main algorithm.
    if event_filtering_info is None:
        print('--- No event filtering-related information for the API being processed ---')
        # If the API being processed does not have any event filtering-related
        # information, then the filtering is considered successful (i.e., the
        # API call is allowed). This facilitates the integration with the
        # analysis code that processes the permissions.
        return True
    # ==============
    # Main algorithm
    # ==============
    print('--- Analysis of API event filtering-related input arguments is about to start... ---')
    # Initialize event filtering manager object
    event_filtering_manager = EventFilteringManagerCls(infrastruc_code_dict,
                                                       service_name,
                                                       handler_name,
                                                       sc_file)
    # Auxiliary set initialization. The following cycle stores an event-filtering
    # result for each event filtering-related input argument.
    event_filtering_results = set()
    # Process all event filtering-related input arguments
    for event_filtering_dict in event_filtering_info:
        # Retrieve event filtering-related input argument name and position
        input_id, input_pos_arg = list(event_filtering_dict.items())[0]
        # ==================================
        # PART 1 - Process API call AST node
        # ==================================
        input_ast_node = get_call_input_ast_node(api_call_ast_node,
                                                 input_id,
                                                 input_pos_arg)
        if input_ast_node is None:
            # Since no information was extracted from the API call AST
            # node, the next step of the cycle can start without any
            # further processing.
            continue
        # =============================================================
        # PART 2 - Process event filtering-related input argument value
        # =============================================================
        if isinstance(input_ast_node, ast.Constant) and isinstance(input_ast_node.value, str):
            # The relevant API input argument is a string literal
            event_filtering_results.add(event_filtering_manager.get_event_filtering_result(input_ast_node.value,
                                                                                           'resolved'))
        elif isinstance(input_ast_node, ast.Name):
            # The relevant API input argument is variable
            event_filtering_results.add(event_filtering_manager.get_event_filtering_result(input_ast_node.id,
                                                                                           'unresolved'))
        else:
            # The input argument does not hold a value that can be inspected
            # with the adopted approach. To simplify the integration with the
            # analysis code that processes the permissions, the filtering is
            # considered successful (i.e., the API call is allowed).
            event_filtering_results.add(True)
    # The returned boolean flag takes into account the results
    # obtained for each event filtering-related API input argument.
    return all(event_filtering_results)

def s3_event_filtering_proc_func(input_to_check,
                                 infrastruc_code_dict,
                                 handler_name):
    """
    Function that implements the s3 service-specific event filter
    processing. If input_to_check matches the handler-specific  
    filtering information extracted from the infrastruce code, it
    returns True.
    Input arguments:
    -) input_to_check: String specifying the input to test against
     the service-specific filtering.
    -) infrastruc_code_dict: Dictionary that maps the infrastructure
    code (i.e., the YAML file) of the application under test.
    -) handler_name: String specifying an application handler.
    NOTE: Since event filtering information is not mandatory in
    the infrastructure code (as it depends upon the implementation
    of the application under test), the function returns True when
    this information is not available.
    """
    try:
        # Extract event filtering-related information. Because
        # of the YAML syntax adopted by the Serverless Framework,
        # the following statement extracts a list.
        events_info = infrastruc_code_dict['functions'][handler_name]['events']
        # APPROXIMATION: The following code assumes that there is
        # only one entry for the S3 service within events_info.
        # Using multiple filters for the same service within a
        # given handler does not seem to be a common pattern.
        # Besides, there are some limitations that affect multiple
        # triggers in AWS. See discussion at:
        # https://forum.serverless.com/t/cannot-have-overlapping-suffixes-in-two-rules-if-the-prefixes-are-overlapping-for-the-same-event-type/15852 
        s3_info = (elem for elem in events_info if 's3' in elem)
        s3_filtering_info = [item['s3']['rules'] for item in s3_info if 'rules' in item['s3']][0]
        # The filtering info is available in a list of dictionaries.
        # The list does not have a predetermined number of rules,
        # and each of them has to be inspected. The results of
        # each rule are stored in a set.
        filtering_results = set()
        for rule in s3_filtering_info:
            if 'prefix' in rule:
                filtering_results.add(input_to_check.startswith(rule['prefix']))
            elif 'suffix' in rule:
                filtering_results.add(input_to_check.endswith(rule['suffix']))
        return all(filtering_results)
    except:
        # An exception is raised when the infrastructure code does
        # not specify event filtering-related information.
        return True

# =======
# Classes
# =======
class EventFilteringManagerCls:
    # === Constructor ===
    def __init__(self,
                 infrastruc_code_dict,
                 service_name,
                 handler_name,
                 sc_file):
        """
        Class constructor. Input arguments:
        -) infrastruc_code_dict: Dictionary that maps the infrastructure
        code (i.e., the YAML file) of the application under test.
        -) service_name: String specifying the cloud service to be
        processed.
        -) handler_name: String specifying an application handler.
        -) sc_file: String specifying the full path of the source code
        file to be processed.
        """
        # Initialize attributes (from input arguments)
        self.infrastruc_code_dict = infrastruc_code_dict
        self.service_name = service_name
        self.handler_name = handler_name
        self.sc_file = sc_file
        # Call initialization methods
        self._init_proc_func_dict()

    # === Protected Method ===
    def _init_proc_func_dict(self):
        """
        Method that initializes a dictionary where:
        -) The cloud services are the keys
        -) The processing functions are the values
        The dictionary is used to store information about
        which service-specific function has to be called.
        NOTE: It should be observed that:
        -) When new service-specific processing functions
        are implemented, the dictionary initialization in
        this method has to be updated.
        -) The code of this class assumes that all the
        functions specified in this dictionary have the
        same signature.  
        """
        self.proc_func_dict = dict()
        self.proc_func_dict['s3'] = s3_event_filtering_proc_func

    # === Protected Method ===
    def _get_var_value_from_sc(self, var):
        """
        Method that returns the value for the source code
        variable var (to be specified as string), obtained
        from the AST-based analysis of the source code file.
        If an assignment statement is not identified for the
        specified source code variable, None is returned.
        NOTE: This method only supports simple assignments,
        implemented with the source code variable on the
        left and a string literal on the right. Example:
        -) s3BucketKey = 'upload-folder/my-file.txt'
        """
        with open(self.sc_file, mode='r') as sc_file_obj:
            # Create in-memory data structure
            ast_tree = ast.parse(sc_file_obj.read())
            # Identify ast.Assign nodes to be processed. These have as
            # a target (i.e., on the left-hand side of the assignment)
            # the variable specified as method input argument.
            for assign_node in (node for node in ast.walk(ast_tree)
                                if isinstance(node, ast.Assign) and node.targets[0].id == var):
                # Identify assignment statements where the value (i.e.,
                # on the right-hand side of the assignment) is a string
                # literal.
                if isinstance(assign_node.value, ast.Constant) and isinstance(assign_node.value.value, str):
                    return assign_node.value.value

    # === Method ===
    def get_event_filtering_result(self, input_to_check, check_mode):
        """
        Method that tests the input arguments input_to_check
        against the service-specific filtering. It returns
        True if the filtering is successful (i.e., in the
        context of an API call inputs' analysis, this means 
        that the API call is allowed), False otherwise.
        Input arguments:
        -) input_to_check: String specifying the input to
        test against the service-specific filtering. The
        following cases are supported: string literal (i.e.,
        the passed string is already resolved, and it does
        not require further processing), and variable name
        (i.e., the passed string specifies a source code
        variable, and the code tries to resolve its value).
        -) check_mode: String specifying if input_to_check
        is a resolved or an unresolved string (see above).
        Only the strings 'resolved' and 'unresolved' are
        supported, an exception is raised otherwise.
        """
        # Raise exception if the provided input argument is not supported
        if check_mode not in ('resolved', 'unresolved'):
            raise ValueError(f'Exception raised - Input {check_mode} not supported')
        # Attempt to resolve input argument, if provided as unresolved
        if check_mode == 'unresolved':
            input_to_check = self._get_var_value_from_sc(input_to_check)
            # Check result of variable resolution
            if input_to_check is None:
                # APPROXIMATION: In this case, the attempt to resolve the
                # input argument was unsuccessful. The analysis code does
                # not have enough information to say if the filtering is
                # allowed or not. To avoid false negatives, the filtering
                # is assumed to be successful.
                return True
        # Return result of service-specific processing
        return self.proc_func_dict[self.service_name](input_to_check,
                                                      self.infrastruc_code_dict,
                                                      self.handler_name)
