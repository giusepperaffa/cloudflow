# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.eventmodels.eventobjmodelsharedreslib import ServiceEventObjModelGeneratorCls

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
                 api_call_ast_node):
        # Call base class constructor
        super().__init__(event, api_call_ast_node)

    # === Method ===
    def _get_bucket_arn(self):
        """
        Method used to populate the event object model.
        It relies on an intermediate data structure.
        """
        if self.event_obj_model_data['bucket_arn'] is None:
            return ast.Constant(None)
        else:
            return self.event_obj_model_data['bucket_arn']

    # === Method ===
    def _get_bucket_name(self):
        """
        Method used to populate the event object model.
        It relies on an intermediate data structure.
        """
        if self.event_obj_model_data['bucket_name'] is None:
            return ast.Constant(None)
        else:
            return self.event_obj_model_data['bucket_name']

    # === Method ===
    def _get_event_name(self):
        """
        Method used to populate the event object model.
        It relies on an intermediate data structure.
        """
        return ast.Constant(self.event_obj_model_data['event_name'])

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
                                                    [self._get_event_name(),
                                                     ast.Dict([ast.Constant('bucket'), ast.Constant('object')],
                                                              [ast.Dict([ast.Constant('name'), ast.Constant('arn')],
                                                                        [self._get_bucket_name(), self._get_bucket_arn()]),
                                                                        ast.Dict([ast.Constant('key')],
                                                                                 [self._get_object_key()])])])])])
            return ast_node
        except Exception as e:
            print('--- Exception raised while creating event object model - Details: ---')
            print(f'--- {e} ---')

    # === Method ===
    def _get_object_key(self):
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
        self.event_obj_model_data['event_name'] = self.event
        self.event_obj_model_data['bucket_name'] = None
        self.event_obj_model_data['bucket_arn'] = None
        self.event_obj_model_data['object_key'] = None

    # === Method ===
    def process_api_put_object(self):
        """
        Method to process the API put_object.
        """
        # The API call put_object includes only keyword arguments.
        # Some of them are used to fill in the data structure with
        # the event object model data.
        for keyword in self.api_call_ast_node.keywords:
            # Processing of keyword argument 'Bucket'
            if keyword.arg == 'Bucket':
                self.event_obj_model_data['bucket_name'] = keyword.value
                self.event_obj_model_data['bucket_arn'] = keyword.value
            # Processing of keyword argument 'Key'
            elif keyword.arg == 'Key':
                self.event_obj_model_data['object_key'] = keyword.value

    # === Method ===
    def process_api_upload_file(self):
        """
        Method to process the API upload_file.
        """
        # The API call upload_file includes both positional and
        # keyword arguments. The information required to fill in
        # the data structure with the event object model data is
        # extracted from specific positional arguments only. The
        # following dictionary identifies the position of input
        # argument of interest.
        pos_args_dict = {'Bucket': 1, 'Key': 2}
        for index, arg in enumerate(self.api_call_ast_node.args):
            if index == pos_args_dict['Bucket']:
                self.event_obj_model_data['bucket_name'] = arg
                self.event_obj_model_data['bucket_arn'] = arg
            elif index == pos_args_dict['Key']:
                self.event_obj_model_data['object_key'] = arg
