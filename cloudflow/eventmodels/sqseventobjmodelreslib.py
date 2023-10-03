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
class SQSEventObjModelGeneratorCls(ServiceEventObjModelGeneratorCls):
    """
    Class that generates SQS-specific models of event objects.
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
            # Processing of keyword argument 'QueueUrl'
            if keyword.arg == 'QueueUrl':
                self.set_event_source_arn(keyword.value)
            # Processing of keyword argument 'MessageBody'
            elif keyword.arg == 'MessageBody':
                self.set_message_body(keyword.value)

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
                                [ast.List([ast.Dict([ast.Constant('body'), ast.Constant('eventSourceARN')],
                                                    [self.get_message_body(), self.get_event_source_arn()])])])
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
    def get_message_body(self):
        """
        Method used to populate the event object model.
        It relies on an intermediate data structure.
        """
        if self.event_obj_model_data['message_body'] is None:
            return ast.Constant(None)
        else:
            return self.event_obj_model_data['message_body']

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
        self.event_obj_model_data['message_body'] = None

    # === Method ===
    @preprocess_api_call
    def process_api_send_message(self):
        """
        Method to process the API put_object.
        """
        # The API call put_object includes only keyword arguments,
        # which are processed by the decorator function. No further
        # processing is required.
        pass

    # === Method ===
    def process_interm_queue(self):
        """
        Method to process intermediate object of type Queue.
        """
        # The initialization of a Queue object requires
        # only one input argument. The related information
        # is stored in the following auxiliary variables.
        kw_arg_name = 'url'
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
    def set_message_body(self, value):
        if self.event_obj_model_data['message_body'] is None:
            self.event_obj_model_data['message_body'] = value
