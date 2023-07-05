# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.eventmodels.s3eventobjmodelreslib import S3EventObjModelGeneratorCls

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
