# =======
# Classes
# =======
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
