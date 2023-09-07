# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.eventmodels.eventobjmodelsharedreslib import ServiceEventObjModelGeneratorCls, preprocess_api_call

# =======
# Classes
# =======
class S3EventObjModelGeneratorCls(ServiceEventObjModelGeneratorCls):
    """
    Class that generates S3-specific models of event objects.
    """
    # === Constructor ===
    def __init__(self,
                 event,
                 api_call_ast_node,
                 interm_interf_record_set,
                 interm_obj_config_dict):
        # Call base class constructor
        super().__init__(event,
                         api_call_ast_node,
                         interm_interf_record_set,
                         interm_obj_config_dict)

    # === Method ===
    def analyse_api_call_kw_args(self):
        """
        Method used to analyse the API call keyword arguments.
        """
        for keyword in self.api_call_ast_node.keywords:
            # Processing of keyword argument 'Bucket'
            if keyword.arg == 'Bucket':
                self.set_bucket_name(keyword.value)
                self.set_bucket_arn(keyword.value)
            # Processing of keyword argument 'Key'
            elif keyword.arg == 'Key':
                self.set_object_key(keyword.value)

    # === Method ===
    def get_bucket_arn(self):
        """
        Method used to populate the event object model.
        It relies on an intermediate data structure.
        """
        if self.event_obj_model_data['bucket_arn'] is None:
            return ast.Constant(None)
        else:
            return self.event_obj_model_data['bucket_arn']

    # === Method ===
    def get_bucket_name(self):
        """
        Method used to populate the event object model.
        It relies on an intermediate data structure.
        """
        if self.event_obj_model_data['bucket_name'] is None:
            return ast.Constant(None)
        else:
            return self.event_obj_model_data['bucket_name']

    # === Method ===
    def get_event_obj_model(self):
        """
        Method that returns the event object model as instance
        of class ast.Dict. The returned AST node is created
        after populating the reference event object model with
        the results of the API-specific processing.
        NOTE: If an exception is raised, None is returned.
        """
        try:
            ast_node = ast.Dict([ast.Constant('Records')],
                                [ast.List([ast.Dict([ast.Constant('eventName'), ast.Constant('s3')],
                                                    [self.get_event_name(),
                                                     ast.Dict([ast.Constant('bucket'), ast.Constant('object')],
                                                              [ast.Dict([ast.Constant('name'), ast.Constant('arn')],
                                                                        [self.get_bucket_name(), self.get_bucket_arn()]),
                                                                        ast.Dict([ast.Constant('key')],
                                                                                 [self.get_object_key()])])])])])
            return ast_node
        except Exception as e:
            print('--- Exception raised while creating event object model - Details: ---')
            print(f'--- {e} ---')

    # === Method ===
    def get_object_key(self):
        """
        Method used to populate the event object model.
        It relies on an intermediate data structure.
        """
        if self.event_obj_model_data['object_key'] is None:
            return ast.Constant(None)
        else:
            return self.event_obj_model_data['object_key']

    # === Method ===
    def init_model_data_dict(self):
        """
        Method that initializes the intermediate data
        structure that is used to populate the event
        reference model. API-specific processing methods
        have to be designed to store their results in
        this data data structure.
        """
        self.event_obj_model_data = dict()
        self.event_obj_model_data['bucket_name'] = None
        self.event_obj_model_data['bucket_arn'] = None
        self.event_obj_model_data['object_key'] = None

    # === Method ===
    def preprocess_api_upload_file(self):
        """
        Method to preprocess the API upload_file.
        """
        # List of positional arguments required by the API
        # when it is called on boto3 client object.
        pos_args_list = ['Filename', 'Bucket', 'Key']
        # NOTE: The above list has to be preprocessed because when
        # the API is called on an intermediate object, e.g. Bucket,
        # the number of positional arguments and, consequently,
        # their positions are different. This is because some
        # pieces of information are passed to the intermediate
        # object constructor rather than to the actual API call.
        # To detect if an intermediate object has already provided
        # information required for the event object model, the
        # data structure holding that information is is checked.
        if self.event_obj_model_data['bucket_name'] is not None:
            pos_args_list.remove('Bucket')
        if self.event_obj_model_data['object_key'] is not None:
            pos_args_list.remove('Key')
        pos_args_dict = {pos_arg: index for index, pos_arg in enumerate(pos_args_list)}
        return pos_args_dict

    # === Method ===
    @preprocess_api_call
    def process_api_put_object(self):
        """
        Method to process the API put_object.
        """
        # The API call put_object includes only keyword arguments,
        # which are processed by the decorator function. No further
        # processing is required.
        pass

    # === Method ===
    @preprocess_api_call
    def process_api_upload_file(self):
        """
        Method to process the API upload_file.
        """
        # The API call upload_file supports both keyword and
        # positional arguments. The keyword arguments are
        # processed by the decorator function, whereas the
        # positional arguments are processed by the code in
        # this method.
        pos_args_dict = self.preprocess_api_upload_file()
        # Processing of the positional arguments
        for index, arg in enumerate(self.api_call_ast_node.args):
            if index == pos_args_dict.get('Bucket', None):
                self.set_bucket_name(arg)
                self.set_bucket_arn(arg)
            elif index == pos_args_dict.get('Key', None):
                self.set_object_key(arg)

    # === Method ===
    def process_interm_bucket(self):
        """
        Method to process intermediate object of type Bucket.
        """
        # The initialization of a Bucket object requires
        # only one input argument. The related information
        # is stored in the following auxiliary variables.
        kw_arg_name = 'name'
        pos_arg_index = 0
        # Process keyword arguments
        try:
            extracted_value = [keyword.value for keyword in
                               self.interm_interf_record.keywords if keyword.arg == kw_arg_name][0]
            self.set_bucket_name(extracted_value)
            self.set_bucket_arn(extracted_value)
        except:
            print('--- No value extracted from keyword arguments ---')
        # Process positional arguments
        try:
            self.set_bucket_name(self.interm_interf_record.args[pos_arg_index])
            self.set_bucket_arn(self.interm_interf_record.args[pos_arg_index])
        except:
            print('--- No value extracted from positional arguments ---')

    # === Method ===
    def process_interm_object(self):
        """
        Method to process intermediate object of type Object.
        """
        # The initialization of a Object object requires
        # two input arguments. The related information
        # is stored in the following auxiliary variable.
        pos_args_dict = {'bucket_name': 0, 'key': 1}
        # Process keyword arguments
        for keyword in self.interm_interf_record.keywords:
            if keyword.arg == 'bucket_name':
                self.set_bucket_name(keyword.value)
                self.set_bucket_arn(keyword.value)
            elif keyword.arg == 'key':
                self.set_object_key(keyword.value)
        # Process positional arguments
        for index, arg in enumerate(self.interm_interf_record.args):
            if index == pos_args_dict['bucket_name']:
                self.set_bucket_name(arg)
                self.set_bucket_arn(arg)
            elif index == pos_args_dict['key']:
                self.set_object_key(arg)

    # === Method ===
    def set_bucket_name(self, value):
        if self.event_obj_model_data['bucket_name'] is None:
            self.event_obj_model_data['bucket_name'] = value

    # === Method ===
    def set_bucket_arn(self, value):
        if self.event_obj_model_data['bucket_arn'] is None:
            self.event_obj_model_data['bucket_arn'] = value

    # === Method ===
    def set_object_key(self, value):
        if self.event_obj_model_data['object_key'] is None:
            self.event_obj_model_data['object_key'] = value
