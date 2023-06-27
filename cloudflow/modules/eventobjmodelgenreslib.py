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
        are implemented, the 
        """
        self.serv_cls_dict = dict()
        self.serv_cls_dict['s3'] = S3EventObjModelGeneratorCls

# ==============================
# Cloud Service-specific Classes
# ==============================
class ServiceEventObjModelGeneratorCls:
    """
    Base to be used for cloud service-specific classes
    that generate event object models.
    """
    def get_event_obj_model(self):
        raise NotImplementedError('Method get_event_obj_model not implemented')

class S3EventObjModelGeneratorCls(ServiceEventObjModelGeneratorCls):
    """
    Class that generates S3-specific models of event objects.
    """
    # === Constructor ===
    def __init__(self, event, api_call_ast_node):
        pass
    
    # === Method ===
    def get_event_obj_model(self):
        pass
