# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast
import os

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.eventmodels.s3eventobjmodelreslib import S3EventObjModelGeneratorCls
from cloudflow.eventmodels.dynamodbeventobjmodelreslib import DynamodbEventObjModelGeneratorCls
from cloudflow.utils.fileprocessingreslib import extract_dict_from_yaml

# =======
# Classes
# =======
class EventObjModelGeneratorCls:
    """
    Class that generates models of event objects.
    """
    # === Constructor ===
    def __init__(self, service, event, api_call_ast_node, interm_interf_record_set):
        assert isinstance(api_call_ast_node, ast.Call), \
            f'--- Instance of class {self.__class__.__name__} cannot be created ---'
        # Attribute initialization
        self.service = service
        self.event = event 
        self.api_call_ast_node = api_call_ast_node
        self.interm_interf_record_set = interm_interf_record_set
        # Additional initialization steps
        self.init_serv_cls_dict()
        self.init_interm_obj_config_dict()
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
                                                                   self.api_call_ast_node,
                                                                   self.interm_interf_record_set,
                                                                   self.interm_obj_config_dict)
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
    def init_interm_obj_config_dict(self,
                                    config_folder='config',
                                    config_file='interm_obj_config_file.yml'):
        """
        Method that maps the configuration file dedicated to the
        intermediate objects (i.e., the boto3 sub-resources) into
        a dictionary, which is stored in an instance variable.
        """
        # Full path of the folder containing the configuration file
        config_folder_full_path = os.path.join(os.sep.join(__file__.split(os.sep)[:-2]), config_folder)
        # The service-specific part of the configuration file is
        # mapped into a dictionary and stored in an instance variable
        self.interm_obj_config_dict = extract_dict_from_yaml(config_folder_full_path,
                                                             config_file).get(self.service, {})

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
        self.serv_cls_dict['dynamodb'] = DynamodbEventObjModelGeneratorCls
