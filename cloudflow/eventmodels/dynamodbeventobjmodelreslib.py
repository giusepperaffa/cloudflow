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
class DynamodbEventObjModelGeneratorCls(ServiceEventObjModelGeneratorCls):
    """
    Class that generates Dynamodb-specific models of event objects.
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
            # Processing of keyword argument 'Item'
            if keyword.arg == 'Item':
                self.set_dynamodb_keys(keyword.value)
                self.set_dynamodb_new_image(keyword.value)
            # Processing of keyword argument 'TableName'
            elif keyword.arg == 'TableName':
                self.set_event_source_arn(keyword.value)

    # === Method ===
    def get_dynamodb_keys(self):
        """
        Method used to populate the event object model.
        It relies on an intermediate data structure.
        """
        if self.event_obj_model_data['dynamodb_keys'] is None:
            return ast.Constant(None)
        else:
            return self.event_obj_model_data['dynamodb_keys']

    # === Method ===
    def get_dynamodb_new_image(self):
        """
        Method used to populate the event object model.
        It relies on an intermediate data structure.
        """
        if self.event_obj_model_data['dynamodb_new_image'] is None:
            return ast.Constant(None)
        else:
            return self.event_obj_model_data['dynamodb_new_image']

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
                                [ast.List([ast.Dict([ast.Constant('eventName'),
                                                     ast.Constant('eventSourceARN'),
                                                     ast.Constant('dynamodb')],
                                                    [self.get_event_name(),
                                                     self.get_event_source_arn(),
                                                     ast.Dict([ast.Constant('Keys'), ast.Constant('NewImage')],
                                                              [self.get_dynamodb_keys(), self.get_dynamodb_new_image()])])])])
            return ast_node
        except Exception as e:
            print('--- Exception raised while creating event object model - Details: ---')
            print(f'--- {e} ---')

    # === Method ===
    def get_event_source_arn(self):
        """
        Method used to populate the event object model.
        It relies on an intermediate data structure.
        """
        if self.event_obj_model_data['event_source_arn'] is None:
            return ast.Constant(None)
        else:
            return self.event_obj_model_data['event_source_arn']

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
        self.event_obj_model_data['event_source_arn'] = None
        self.event_obj_model_data['dynamodb_keys'] = None
        self.event_obj_model_data['dynamodb_new_image'] = None

    # === Method ===
    @preprocess_api_call
    def process_api_put_item(self):
        """
        Method to process the API put_item.
        """
        # The API call put_item includes only keyword arguments,
        # which are processed by the decorator function. No further
        # processing is required.
        pass

    # === Method ===
    def process_interm_table(self):
        """
        Method to process intermediate object of type Table.
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
            self.set_event_source_arn(extracted_value)
        except:
            print('--- No value extracted from keyword arguments ---')
        # Process positional arguments
        try:
            self.set_event_source_arn(self.interm_interf_record.args[pos_arg_index])
        except:
            print('--- No value extracted from positional arguments ---')

    # === Method ===
    def set_event_source_arn(self, value):
        if self.event_obj_model_data['event_source_arn'] is None:
            self.event_obj_model_data['event_source_arn'] = value

    # === Method ===
    def set_dynamodb_keys(self, value):
        if self.event_obj_model_data['dynamodb_keys'] is None:
            self.event_obj_model_data['dynamodb_keys'] = value

    # === Method ===
    def set_dynamodb_new_image(self, value):
        if self.event_obj_model_data['dynamodb_new_image'] is None:
            self.event_obj_model_data['dynamodb_new_image'] = value
