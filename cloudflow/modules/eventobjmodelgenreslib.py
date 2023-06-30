# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast

# =======
# Classes
# =======
class EventObjModelGeneratorCls:
    """
    Class that generates models of event objects.
    """
    # === Constructor ===
    def __init__(self, service, event, api_call_ast_node):
        assert isinstance(api_call_ast_node, ast.Call), \
            f'--- Instance of class {self.__class__.__name__} cannot be created ---'
        # Attribute initialization
        self.service = service
        self.event = event 
        self.api_call_ast_node = api_call_ast_node
        # Additional initialization steps
        self.init_serv_cls_dict()
        self.create_serv_model_gen()

    # === Method ===
    def create_serv_model_gen(self):
        """
        Method that instantiates the service-specific event
        model generator class. A dictionary stored in an
        instance variable is used to identify the class.  
        """
        try:
            self.serv_model_gen = self.serv_cls_dict[self.service](self.event,
                                                                   self.api_call_ast_node)
        except KeyError as e:
            print(f'--- The service {e} is not supported ---')
    
    # === Method ===
    def get_event_obj_model(self):
        """
        Method that returns the service-specific event object model. 
        """
        try:
            return self.serv_model_gen.get_event_obj_model()
        except Exception as e:
            print('--- Exception raised while creating event object model - Details: ---')
            print(f'--- {e} ---')

    # === Method ===
    def init_serv_cls_dict(self):
        """
        Method that initializes a dictionary the maps the cloud
        service to a class that generates a service-specific
        event object. NOTE: When new service-specific classes
        are implemented, the dictionary initialization in this
        method has to be updated.
        """
        self.serv_cls_dict = dict()
        self.serv_cls_dict['s3'] = S3EventObjModelGeneratorCls

# ==============================
# Cloud Service-specific Classes
# ==============================
class ServiceEventObjModelGeneratorCls:
    """
    Base class to be used for cloud service-specific
    classes that generate event object models.
    """
    # === Constructor ===
    def __init__(self, event, api_call_ast_node):
        # Attribute initialization
        self.event = event
        self.api_call_ast_node = api_call_ast_node
        # Processing steps needed to obtain the event object model
        self.init_model_data_dict()
        self.process_api_call()

    # === Method ===
    def get_event_obj_model(self):
        """
        Method to be implemented in the child class,
        otherwise an exception is raised.
        """
        raise NotImplementedError('Method get_event_obj_model not implemented')

    # === Method ===
    def init_model_data_dict(self):
        """
        Method to be implemented in the child class,
        otherwise an exception is raised.
        """
        raise NotImplementedError('Method init_model_data_dict not implemented')

    # === Method ===
    def process_api_call(self):
        """
        Method that triggers the processing of the API call
        by automatically identifying API-specific methods
        in the class. If an API call is not supported (i.e.,
        no dediicated method is included in the class) an
        exception is raised.
        """
        try:
            # The API name is extracted from the API ast node
            api_name = self.api_call_ast_node.func.attr
            print(f'--- API {api_name} being processed... ---')
            # API-specific method is identfied and executed.
            # NOTE: The following statement relies on a
            # naming convention that must be adopted by the
            # API-specific methods
            getattr(self, 'process_api_' + api_name)()
        except AttributeError as e:
            print(f'--- {e} ---')
        except Exception as e:
            print('--- Exception raised during API processing - Details: ---')
            print(f'--- {e} ---')

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
