# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast
import os

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.utils.fileprocessingreslib import extract_dict_from_json

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
        are implemented, the 
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
    def __init__(self, event, api_call_ast_node, ref_model_file):
        # Attribute initialization
        self.event = event
        self.api_call_ast_node = api_call_ast_node
        self.ref_model_file = ref_model_file
        # Processing steps needed to obtain the event object model
        self.init_model_data_dict()
        self.upload_ref_model()
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

    # === Method ===
    def upload_ref_model(self, folder='event-models'):
        """
        Method that uploads the reference model for the
        event object of the service. Reference models
        provide the structure of the event objects and
        need to be populated by processing the relevant
        API call.
        """
        # Full path of the folder with reference event object files
        ref_model_folder = os.path.join(os.sep.join(__file__.split(os.sep)[:-2]), folder)
        # Map reference model into a dictionary
        self.ref_model_dict = extract_dict_from_json(ref_model_folder, self.ref_model_file)

class S3EventObjModelGeneratorCls(ServiceEventObjModelGeneratorCls):
    """
    Class that generates S3-specific models of event objects.
    """
    # === Constructor ===
    def __init__(self,
                 event,
                 api_call_ast_node,
                 ref_model_file='s3_event.json'):
        # Call base class constructor
        super().__init__(event, api_call_ast_node, ref_model_file)

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
            # Auxiliary variable init (improved readability)
            model_record = self.ref_model_dict['Records'][0]
            # Update fields of the event object reference model
            model_record['eventName'] = self.event_obj_model_data['event_name']
            model_record['s3']['bucket']['name'] = self.event_obj_model_data['bucket_name']
            model_record['s3']['bucket']['arn'] = self.event_obj_model_data['bucket_arn']
            model_record['s3']['object']['key'] = self.event_obj_model_data['object_key']
            # Populated event object model dictionary is mapped
            # into an AST Expression. Its attribute body includes
            # the required ast.Dict instance.
            ast_expression_node = ast.parse(str(self.ref_model_dict), mode='eval')
            return ast_expression_node.body
        except KeyError as e:
            print('--- Exception raised while creating event object model ---')
            print(f'--- The Key {e} is missing from one of the processed dictionaries ---')
        except Exception as e:
            print('--- Exception raised while creating event object model - Details: ---')
            print(f'--- {e} ---')

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
        pass
