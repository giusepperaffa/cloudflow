# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast
import astor
import collections
import os
import yaml

# =========
# Functions
# =========
def get_api_lineno_set(ast_tree, interf_record):
    """
    Function that processes the passed AST tree (in-memory data
    structure) and returns in a set the lines of code containing
    API calls on the interface object the interf_record input
    refers to. The function processes the entire AST tree to
    gather the required information, and it does not rely on
    the order AST nodes are yielded by ast.walk.
    NOTE: The function detects API calls made either directly on
    the interface object, e.g., s3_client.upload_file(...), where
    s3_client is the interface object, or indirectly via an
    intermediate object or API, e.g.:
    s3_client.Object(...).upload_file(...)
    """
    # Initialize set returned by the function
    api_lineno_set = set()
    # Process AST tree (in-memory data structure)
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.Call):
            try:
                if interf_record.instance_name == node.func.value.id:
                    api_lineno_set.add(node.lineno)
            except:
                pass
    return api_lineno_set

def get_events_handlers_dict(handlers_dict):
    """
    Function that reverses the mapping implemented in the handlers
    dictionary provided by the HandlersEventsIdentifierCls class
    (module handlerseventsreslib). Reversing the mapping passed as
    input argument facilitates the retrieval of the all the handlers
    triggered by a given event. The returned data structure has
    service event tuples as keys a sets of handlers as values.
    """
    # Initialization of the returned data structure
    events_handlers_dict = collections.defaultdict(set)
    for handler, service_event_set in handlers_dict.items():
        # The tuples processed within this nested for cycle will
        # become the keys of the returned dictionary
        for service_event_tuple in service_event_set:
            events_handlers_dict[service_event_tuple].add(handler)
    return events_handlers_dict

# =======
# Classes
# =======
class CodeSynInjManagerCls:
    """
    Class that provides the functionality to add synthesized
    handler calls to the analysed repository to simulate a
    synchronous-like execution flow. The class relies on data
    structures provided by other modules of the tool. 
    """
    # === Constructor ===
    def __init__(self,
                 interf_objs_dict,
                 perm_dict,
                 handlers_dict,
                 infrastruc_code_dict):
        """
        Class constructor.
        """
        # Data structure with information about interface objects 
        self.interf_objs_dict = interf_objs_dict
        # Data structure containing permissions-related information
        self.perm_dict = perm_dict
        # Data structure containing handlers-related information
        self.handlers_dict = handlers_dict
        # Data structure containing the infrastructure code dictionary
        self.infrastruc_code_dict = infrastruc_code_dict

    # === Protected Method ===
    def _get_source_code_info(self):
        """
        Method that implements a generator processing information
        extracted from the data structure dedicated to the
        interface objects. A tuple with the following elements
        is yielded:
        1) Full path of source code file.
        2) Data structure with information on interface objects
        in source code file.
        """
        for import_mode in self.interf_objs_dict:
            for sc_file in self.interf_objs_dict[import_mode]:
                yield sc_file, self.interf_objs_dict[import_mode][sc_file]

    # === Protected Method ===
    def _read_config_file(self,
                          config_folder='config',
                          config_file='api_info_config_file.yml'):
        """
        Method that maps the configuration file dedicated to the
        interface module API information into a dictionary, which
        is stored in an instance variable and returned. 
        """
        # Full path of the folder containing the configuration file
        config_folder_full_path = os.path.join(os.sep.join(__file__.split(os.sep)[:-2]), config_folder)
        # The configuration file is mapped into a dictionary and returned
        with open(os.path.join(config_folder_full_path, config_file), mode='r') as config_file_obj:
            self.config_dict = yaml.load(config_file_obj, Loader=yaml.BaseLoader)
        return self.config_dict

    # === Method ===
    def inject_synthesized_code(self):
        """
        Method that injects synthesized code to simulate a
        synchronous-like execution flow.
        """
        for sc_file, interf_objs_info_list in self._get_source_code_info():
            print('--- The following file is about to be processed: ---')
            print(f'--- {sc_file} ---')
            for interf_record in interf_objs_info_list:
                # Adds synthesized code within in-memory data structure
                with open(sc_file, mode='r') as sc_file_obj:
                    tree = ast.parse(sc_file_obj.read())
                    # Get set of lines of code where API calls made on the
                    # interface object interf_record refers to. Obtaining
                    # these lines of code before modifying the source code
                    # is necessary because the order in which AST nodes are
                    # processed is NOT guaranteed.
                    api_lineno_set = get_api_lineno_set(tree, interf_record)
                    # Create instance of class that modifies the source code
                    walker = CodeSynthesisInjectionCls(interf_record,
                                                       self.perm_dict,
                                                       self.handlers_dict,
                                                       self.infrastruc_code_dict,
                                                       self._read_config_file(),
                                                       sc_file,
                                                       api_lineno_set)
                    walker.walk(tree)
                # Overwrite source code file to include synthesized code
                with open(sc_file, mode='w') as sc_file_obj:
                    sc_file_obj.write(astor.to_source(tree))

class CodeSynthesisInjectionCls(astor.TreeWalk):
    """
    Class that customizes the tree traversal implemented by
    the base class astor.TreeWalk to inject a function call
    after another function call. This code was implemented
    using the example available in question 41764207 on Stack
    Overflow as baseline.
    """
    # === Constructor ===
    def __init__(self,
                 interf_record,
                 perm_dict,
                 handlers_dict,
                 infrastruc_code_dict,
                 config_dict,
                 sc_file,
                 api_lineno_set):
        """
        Class constructor.
        """
        # NOTE: Calling the base class constructor with the command
        # super().__init__() causes initialization problems, as the
        # constructor of the class at the top of the hierarchy is
        # presumably called.
        astor.TreeWalk.__init__(self)
        # Initialization of additional attributes
        self.interf_record = interf_record
        self.perm_dict = perm_dict
        self.handlers_dict = handlers_dict
        self.infrastruc_code_dict = infrastruc_code_dict
        self.config_dict = config_dict
        self.sc_file = sc_file
        self.api_lineno_set = api_lineno_set

    # === Protected Method ===
    def _check_api_permissions(self,
                              service,
                              interf_obj_type,
                              api_name):
        """
        Method that checks whether the permissions required for
        the execution of the specified API are present in the
        repository infrastructure code file. If so, the API can
        be executed and True is returned, False otherwise.
        NOTE: This method must be run only on APIs specified in
        the tool config file, otherwise an unhandled exception
        is raised.
        """
        # Required permissions for the API are extracted from configuration dictionary  
        required_permissions = set(self.config_dict[service][interf_obj_type + '_obj'][api_name]['permissions'])
        # If the intersection between the required permissions and those specified
        # in the repository infrastructure code YAML file is a non-empty set, then
        # the execution of the API is allowed.    
        return (required_permissions & self.perm_dict[service]) != set([])

    # === Protected Method ===
    def _check_api_support(self,
                           service,
                           interf_obj_type,
                           api_name):
        """
        Method that checks whether the specified API for a given
        service and a given interface object type (i.e., client
        or resource) is present in the configuration file. If so,
        True is returned, False otherwise.
        """
        try:
            return api_name in self.config_dict[service][interf_obj_type + '_obj']
        except KeyError as e:
            print(f'--- API {api_name} could not be checked in the configuration file ---')
            print(f'--- The following tag is missing in the configuration file: ---')
            print(f'--- {e} ---')
            return False

    # === Protected Method ===
    def _get_handler_qual_name(self, handler_name):
        """
        Method that obtains the handler qualified name in preparation
        for code synthesis. The implementation relies on the dictionary
        mapping the infrastructure code.
        """
        handler_qual_name = self.infrastruc_code_dict['functions'][handler_name]['handler'].split('/')[-1]
        if handler_qual_name.split('.')[0] == os.path.splitext(os.path.basename(self.sc_file))[0]:
            # When the above condition is met, the handler to be called is
            # included in the source code file being processed. Therefore,
            # prepending the name of the module containing the handler is
            # not necessary, and it will be removed.
            return handler_qual_name.split('.')[1]
        else:
            return handler_qual_name

    # === Protected Method ===
    def _get_syn_code(self, service, interf_obj_type, api_name):
        """
        Method that implements a generator that yields a tuple with
        the following elements:
        1) AST node corresponding to the event object initialization
        statement. A model for the event object is used, rather than
        a full initialization.
        2) AST node corresponding to the synthesized handler call.
        NOTE: When an exception is raised, this generator yields the
        tuple (None, None).
        """
        # To facilitate the retrieval of the handlers triggered by a
        # a given event, the handlers dictionary stored in one of the
        # instance variables is first processed with a function.
        events_handlers_dict = get_events_handlers_dict(self.handlers_dict)
        # The logic implemented in this method takes into account that
        # a given API call can trigger multiple events, and for each of
        # them code synthesis and injection are potentially needed.
        for event in self.config_dict[service][interf_obj_type + '_obj'][api_name]['events']:
            try:
                for handler in events_handlers_dict[(service, event)]:
                    handler_qual_name = self._get_handler_qual_name(handler)
                    # Synthetize event object initialization
                    event_obj_init_stmt = self._syn_event_obj_init_stmt(service, event)
                    # Synthetize handler call
                    syn_handler_call = self._syn_handler_call(handler_qual_name)
                    yield event_obj_init_stmt, syn_handler_call
            except:
                yield None, None

    # === Protected Method ===
    def _syn_event_obj_init_stmt(self, service, event):
        """
        Method that synthesizes and returns the AST node containing
        the event object initialization.
        """
        print('--- Synthesis of the event object initialization is incomplete ---')
        ast_node = ast.Assign(targets=[ast.Name(id="event", ctx=ast.Store())],
                              value=ast.Dict([ast.Name('Test', ast.Load())],
                                             [ast.Name('Test', ast.Load())]))
        return ast_node

    # === Protected Method ===
    def _syn_handler_call(self, handler_qual_name):
        """
        Method that synthesizes and returns the AST node containing
        a handler call.
        """
        # Depending on whether the qualified handler name passed
        # as input argument includes a module name, a different
        # AST node, part of the returned one, is initialized.
        if '.' in handler_qual_name:
            handler_func = ast.Attribute(value=ast.Name(id=handler_qual_name.split('.')[0], ctx=ast.Load()),
                                         attr=handler_qual_name.split('.')[1], ctx=ast.Load())
        else:
            handler_func = ast.Name(handler_qual_name, ast.Load())
        # Arguments of the handler call
        args = [ast.Name(id='event', ctx=ast.Load()), ast.Name(id='context', ctx=ast.Load())]
        return ast.Expr(ast.Call(handler_func, args, []))

    # === Method ===
    def pre_body_name(self):
        """
        Method that inserts synthesized code in the tree data structure.
        """
        body = self.cur_node
        # NOTE: Auxiliary counter to consistently modify in place
        # the tree data structure. This is due to the fact that the
        # main for loop implemented in this method iterates through
        # a copy of the list body. The counter is initialized to 1
        # to ensure that the synthesized code is added after the
        # relevant API call.
        counter = 1
        for i, child in enumerate(body[:]):
            self.__api_to_process = None
            # The method pre_Call is automatically called when the
            # method walk, provided by the base class, is executed.
            self.walk(child)
            if self.__api_to_process is not None:
                for event_obj_init_stmt, syn_handler_call in self._get_syn_code(self.interf_record.service,
                                                                                self.interf_record.instance_type,
                                                                                self.__api_to_process):
                    if all([event_obj_init_stmt is not None, syn_handler_call is not None]):
                        # Inject synthesized code with initialization of event object
                        body.insert(i + counter, event_obj_init_stmt)
                        # Increment auxiliary counter
                        counter += 1
                        # Inject synthesized code with handler call
                        body.insert(i + counter, syn_handler_call)
                        # Increment auxiliary counter
                        counter += 1
        self.__api_to_process = None
        return True

    # === Method ===
    def pre_Call(self):
        """
        Method that processes instances of the class Call (module ast).
        Such instances have a func attribute, which normally is a Name
        or an Attribute object. Since the purpose of the class is to
        inject code after API calls on an interface object, the code
        assumes that the func attribute is an Attribute object. For  
        further information on the Call class of the Standard Library
        module ast, refer to:
        https://greentreesnakes.readthedocs.io/en/latest/nodes.html#Call
        """
        # The purpose of this method is to initialize the following
        # private attribute. When the initialization is not possible
        # or fails, the default value will remain unchanged.
        self.__api_to_process = None
        try:
            # Check line of code number and if API call is supported
            if all([self.cur_node.lineno in self.api_lineno_set,
                    self._check_api_support(self.interf_record.service,
                                            self.interf_record.instance_type,
                                            self.cur_node.func.attr)]):
                # Check permissions required to execute the API call
                print(f'--- Permissions for API {self.cur_node.func.attr} being checked... ---')
                if self._check_api_permissions(self.interf_record.service,
                                               self.interf_record.instance_type,
                                               self.cur_node.func.attr):
                    self.__api_to_process = self.cur_node.func.attr
                else:
                    print('--- Permissions for API {self.cur_node.func.attr} not found - No code injected ---')
        except AttributeError:
            # This exception is raised every time the func attribute of
            # the of Call object is not an Attribute object. To avoid
            # noisy log files, no message is printed in this case.
            pass 
        except Exception as e:
            print('--- Exception raised during code synthesis and injection - Details: ---')
            print(f'--- {e} ---')
        return True
