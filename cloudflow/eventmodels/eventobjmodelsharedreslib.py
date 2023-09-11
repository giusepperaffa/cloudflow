# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast

# =========
# Functions
# =========
def preprocess_api_call(process_api_method):
    """
    Decorator function that executes standard
    preprocessing steps prior to executing
    an API-specific processing method.
    """
    def wrapper(*args, **kwargs):
        print('--- Preprocessing steps are about to be executed... ---')
        args[0].process_all_interm_interf_records()
        args[0].analyse_api_call_kw_args()
        process_api_method(*args, **kwargs)
    return wrapper

# =======
# Classes
# =======
class ServiceEventObjModelGeneratorCls:
    """
    Base class to be used for cloud service-specific
    classes that generate event object models.
    """
    # === Constructor ===
    def __init__(self,
                 event,
                 api_call_ast_node,
                 interm_interf_record_set,
                 interm_obj_config_dict):
        # Attribute initialization
        self.event = event
        self.api_call_ast_node = api_call_ast_node
        self.interm_interf_record_set = interm_interf_record_set
        self.interm_obj_config_dict = interm_obj_config_dict
        # Processing steps needed to obtain the event object model
        self.init_model_data_dict()
        self.process_api_call()

    # === Method ===
    def analyse_api_call_kw_args(self):
        """
        Method to be implemented in the child class,
        otherwise an exception is raised.
        """
        raise NotImplementedError('Method analyse_api_call_kw_args not implemented')

    # === Method ===
    def get_event_name(self):
        """
        Method used to populate the event object model.
        """
        return ast.Constant(self.event)

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
    def process_all_interm_interf_records(self):
        """
        Method that triggers the processing of intermediate objects
        (boto3 sub-resources) by automatically identifying intermediate
        object-specific methods in the class. If an intermediate object
        is not supported (i.e., no dedicated method is included in the
        class) an exception is raised.
        """
        # Auxiliary dictionary to store all the intermediate object
        # interface records organized by origin.
        interm_interf_record_dict = dict()
        # Identify intermediate object interface record (same line of code)
        try:
            interm_interf_record_dict['line_no'] = [record.ast_node for record in self.interm_interf_record_set
                                                    if record.line_no == self.api_call_ast_node.lineno]
        except:
            print('--- No intermediate interface records retrieved from same line of code ---')
        # Identify intermediate object interface record (intermediate initialization)
        try:
            interm_interf_record_dict['instance_name'] = [record.ast_node for record in self.interm_interf_record_set
                                                          if record.instance_name == self.api_call_ast_node.func.value.id]
        except:
            print('--- No intermediate interface records retrieved through instance name ---')
        # Process all gathered intermediate interface records
        for origin, interm_interf_record_list in interm_interf_record_dict.items():
            if interm_interf_record_list:
                self.interm_interf_record = interm_interf_record_list[0]
                # Check if the intermediate interface record refers to a relevant intermediate object
                if self.interm_interf_record.func.attr in self.interm_obj_config_dict:
                    try:
                        print(f"--- Intermediate object being processed (from {origin.replace('_', ' ')})... ---")
                        print(f'--- Intermediate object type: {self.interm_interf_record.func.attr} ---')
                        # NOTE: The following statement relies on a naming convention that
                        # must be adopted by the intermediate object-specific methods
                        getattr(self, 'process_interm_' + self.interm_interf_record.func.attr.lower())()
                    except Exception as e:
                        print('--- Exception raised during intermediate object processing - Details: ---')
                        print(f'--- {e} ---')

    # === Method ===
    def process_api_call(self):
        """
        Method that triggers the processing of the API call
        by automatically identifying API-specific methods
        in the class. If an API call is not supported (i.e.,
        no dedicated method is included in the class) an
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
