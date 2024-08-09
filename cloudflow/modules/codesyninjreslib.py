# ========================================
# Import Python Modules (Standard Library)
# ========================================
import ast
import astor
import collections
import os
from typing import Optional, NamedTuple

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.utils.fileprocessingreslib import extract_dict_from_yaml
from cloudflow.modules.eventobjmodelgenreslib import EventObjModelGeneratorCls
from cloudflow.modules.permissionsreslib import analyse_api_permissions, analyse_resource_level_permissions
from cloudflow.modules.eventfilteringreslib import analyse_event_filtering

# =========
# Functions
# =========
def get_api_call_ast_nodes(ast_tree, interf_record):
    """
    Function that processes the passed AST tree (in-memory data
    structure) and returns in a set the ast.Call nodes
    containing direct or indirect API calls on the interface
    object the interf_record input refers to (see examples).
    The function also returns:
    -) A set of intermediate interface objects' records
    -) A dictionary with the ast.Call nodes as keys, and the
    corresponding AST function definition nodes as values.
    The function detects API calls made:
    1) Directly on the interface object, e.g.:
    s3_client.upload_file(...)
    where s3_client is the interface object
    2) Indirectly via an intermediate object or API, e.g.:
    a) s3_client.Object(...).upload_file(...)
    b) s3_obj = s3_client.Object(...); s3_obj.upload_file(...)
    """
    # Initialize set returned by the function
    api_call_ast_nodes = set()
    # Initialize set storing intermediate objects' instance names
    interm_objs_set = set()
    # Initialize set storing intermediate objects' interface records
    interm_interf_record_set = set()
    # Initialize set storing function definition nodes
    func_def_ast_nodes = set()
    # Process AST tree (in-memory data structure)
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.Call):
            try:
                if node.func.value.id in interm_objs_set:
                    api_call_ast_nodes.add(node)
                elif interf_record.instance_name == node.func.value.id:
                    api_call_ast_nodes.add(node)
                    # Store record of intermediate object interface
                    interm_interf_record_set.add(IntermInterfaceRecordCls(
                        line_no=node.lineno,
                        instance_name=None,
                        ast_node=node
                    ))
            except:
                pass
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            try:
                if interf_record.instance_name == node.value.func.value.id:
                    interm_objs_set.update(target.id for target in node.targets)
                    # Store record of intermediate object interface
                    interm_interf_record_set.add(IntermInterfaceRecordCls(
                        line_no=node.value.lineno,
                        instance_name=node.targets[0].id,
                        ast_node=node.value
                    ))
            except:
                pass
        elif isinstance(node, ast.FunctionDef):
            func_def_ast_nodes.add(node)
    # Obtain dictionary that has the identified ast.Call as
    # keys, and their AST function definition nodes as values.
    api_call_func_def_dict = get_api_call_func_def_dict(api_call_ast_nodes,
                                                        func_def_ast_nodes)
    return api_call_ast_nodes, interm_interf_record_set, api_call_func_def_dict

def get_api_call_func_def_dict(api_call_ast_nodes, func_def_ast_nodes):
    """
    Function that processes a set of API call AST nodes and
    a set of AST function definition nodes to determine the
    function a given API call AST node belongs to, if any.
    A dictionary with the API call AST nodes as keys and the
    corresponding AST function definition nodes as values is
    returned. If an API call AST node is not included in any
    of the processed AST function definition nodes, then the
    dictinary value will be None.
    """
    # Initialize dictionary returned by the function
    api_call_func_def_dict = {}
    # The function definition node for each API call AST node
    # is stored as a dictionary value.
    for api_call_ast_node in api_call_ast_nodes:
        for func_def_ast_node in func_def_ast_nodes:
            # To identify the function the API call AST node belongs
            # to, it is necessary to use ast.walk to yield all the
            # descendant nodes. The attribute body of a function
            # definition node only stores the direct children.
            if api_call_ast_node in ast.walk(func_def_ast_node):
                api_call_func_def_dict[api_call_ast_node] = func_def_ast_node
                break
        else:
            # If this branch gets executed, then no function definition
            # code was found for the API call AST node being processed.
            api_call_func_def_dict[api_call_ast_node] = None
    return api_call_func_def_dict

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
                 perm_res_dict,
                 handlers_dict,
                 infrastruc_code_dict,
                 plugin_info):
        """
        Class constructor.
        """
        # Data structure with information about interface objects 
        self.interf_objs_dict = interf_objs_dict
        # Data structure containing permissions-related information
        self.perm_dict = perm_dict
        # Data structure containing permissions-related information
        # for resources explicitly specified in the YAML file.
        self.perm_res_dict = perm_res_dict
        # Data structure containing handlers-related information
        self.handlers_dict = handlers_dict
        # Data structure containing the infrastructure code dictionary
        self.infrastruc_code_dict = infrastruc_code_dict
        # Object containing plugin-specific information
        self.plugin_info = plugin_info

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
        self.config_dict = extract_dict_from_yaml(config_folder_full_path, config_file)
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
                    # Get set of AST nodes with API calls made directly
                    # or indirectly on the interface object interf_record
                    # refers to. Obtaining this information before modifying
                    # the source code is necessary because the order in which
                    # AST nodes are processed is NOT guaranteed.
                    api_call_ast_nodes, interm_interf_record_set, api_call_func_def_dict = \
                        get_api_call_ast_nodes(tree, interf_record)
                    # Create instance of class that modifies the source code
                    walker = CodeSynthesisInjectionCls(interf_record,
                                                       self.perm_dict,
                                                       self.perm_res_dict,
                                                       self.handlers_dict,
                                                       self.infrastruc_code_dict,
                                                       self.plugin_info,
                                                       self._read_config_file(),
                                                       sc_file,
                                                       api_call_ast_nodes,
                                                       interm_interf_record_set,
                                                       api_call_func_def_dict)
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
                 perm_res_dict,
                 handlers_dict,
                 infrastruc_code_dict,
                 plugin_info,
                 config_dict,
                 sc_file,
                 api_call_ast_nodes,
                 interm_interf_record_set,
                 api_call_func_def_dict):
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
        self.perm_res_dict = perm_res_dict
        self.handlers_dict = handlers_dict
        self.infrastruc_code_dict = infrastruc_code_dict
        self.plugin_info = plugin_info
        self.config_dict = config_dict
        self.sc_file = sc_file
        self.api_call_ast_nodes = api_call_ast_nodes
        self.interm_interf_record_set = interm_interf_record_set
        self.api_call_func_def_dict = api_call_func_def_dict
        # Execution of initialization methods
        self._init_instance_vars()

    # === Protected Method ===
    def _check_api_permissions(self,
                               service,
                               interf_obj_type,
                               api_call_ast_node,
                               api_name,
                               function_name):
        """
        Method that checks whether the permissions required for
        the execution of the specified API have been configured.
        If so, the API can be executed and True is returned,
        False otherwise.
        NOTE: This method must be run only on APIs specified in
        the tool config file, otherwise an unhandled exception
        is raised.
        """
        # Required permissions for the API are extracted from configuration dictionary
        required_permissions = set(self.config_dict[service][interf_obj_type + '_obj'][api_name]['permissions'])
        # Resource-related information for the API is extracted from configuration dictionary.
        resource_info = self.config_dict[service][interf_obj_type + '_obj'][api_name].get('resources')
        # Obtain handler name specified in the infrastructure code
        handler_name = self._get_handler_from_function(function_name)
        # Service-specific permissions result
        service_perm_res = analyse_api_permissions(required_permissions,
                                                   self.perm_dict[service],
                                                   service,
                                                   self.plugin_info,
                                                   handler_name)
        # Resource-level permissions result
        resource_level_perm_res = analyse_resource_level_permissions(required_permissions,
                                                                     self.perm_res_dict,
                                                                     service,
                                                                     resource_info,
                                                                     api_call_ast_node,
                                                                     self.infrastruc_code_dict,
                                                                     self.plugin_info,
                                                                     handler_name,
                                                                     self.sc_file)
        return (service_perm_res and resource_level_perm_res)

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
    def _get_handler_from_function(self, function_name):
        """
        Method that retrieves the handler name as specified in
        the infrastructure code file at the first level below
        the functions tag, starting from the actual function
        name. While in most cases the two names match, this is
        not mandatory. Furthermore:
        -) The same function name can be used in multiple
        modules. Therefore, the code in this method processes
        the information on the specific source code file being
        processed to reliably retrieve the handler name.
        -) If no handler is identified, the method returns
        None. This happens when the processed function is
        not an event-triggered handler.
        -) None is returned when an exception is raised.
        """
        try:
            for handler_name in self.infrastruc_code_dict['functions']:
                # Location of the actual function
                handler_loc = self.infrastruc_code_dict['functions'][handler_name]['handler']
                # Name of the folder containing the source code file
                sc_file_folder = os.path.dirname(self.sc_file).split('/')[-1]
                # Source code file name
                sc_file_name = os.path.splitext(os.path.basename(self.sc_file))[0]
                # Process extracted information
                if ('/' in handler_loc) and handler_loc.endswith('/'.join([sc_file_folder,
                                                                           sc_file_name + '.' + function_name])):
                    # When this condition holds true, a path including folder
                    # name and module name is used to identify the function.
                    return handler_name
                elif ('/' not in handler_loc) and handler_loc.endswith(sc_file_name + '.' + function_name):
                    # When this condition holds true, only the module name
                    # is used to identify the function.
                    return handler_name
            else:
                # No handler was identified by the previous cycle
                print(f'--- WARNING: No handler was identified for the function: {function_name} ---')
                return
        except:
            # When an exception is raised, None is returned
            print(f'--- WARNING: No handler was identified for the function: {function_name} ---')
            return

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
    def _get_syn_code(self, service, interf_obj_type, api_call_ast_node, interm_interf_record_set):
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
        # Retrieve API name from AST node
        api_name = api_call_ast_node.func.attr
        # To facilitate the retrieval of the handlers triggered by a
        # a given event, the handlers dictionary stored in one of the
        # instance variables is first processed with a function.
        events_handlers_dict = get_events_handlers_dict(self.handlers_dict)
        # Extract event filtering-related information for the API
        event_filtering_info = self.config_dict[service][interf_obj_type + '_obj'][api_name].get('events_filtering')
        # The logic implemented in this method takes into account that
        # a given API call can trigger multiple events, and for each of
        # them code synthesis and injection are potentially needed.
        for event in self.config_dict[service][interf_obj_type + '_obj'][api_name]['events']:
            try:
                for handler in events_handlers_dict[(service, event)]:
                    # Event filtering result
                    event_filtering_res = analyse_event_filtering(service,
                                                                  event_filtering_info,
                                                                  api_call_ast_node,
                                                                  self.infrastruc_code_dict,
                                                                  handler,
                                                                  self.sc_file)
                    if event_filtering_res:
                        handler_qual_name = self._get_handler_qual_name(handler)
                        # Synthetize event object initialization
                        event_obj_init_stmt = self._syn_event_obj_init_stmt(service,
                                                                            event,
                                                                            api_call_ast_node,
                                                                            interm_interf_record_set)
                        # Synthetize handler call
                        syn_handler_call = self._syn_handler_call(handler_qual_name)
                        yield event_obj_init_stmt, syn_handler_call
                    else:
                        print('--- Event filtering detected - No code injected ---')
                        yield None, None
            except:
                yield None, None

    # === Protected Method ===
    def _init_instance_vars(self):
        """
        Method that initialize instance variables necessary
        to implement the required processing.
        """
        self.api_lineno_set = {api_call_ast_node.lineno for api_call_ast_node in
                               self.api_call_ast_nodes}
        self.api_lineno_func_name_dict = {node.lineno: (None if func_def is None else func_def.name)
                                          for node, func_def in self.api_call_func_def_dict.items()}
        return

    # === Protected Method ===
    def _syn_event_obj_init_stmt(self, service, event, api_call_ast_node, interm_interf_record_set):
        """
        Method that synthesizes and returns the AST node containing
        the event object initialization.
        """
        print('--- Synthesis of the event object is about to start... ---')
        event_obj_model_gen = EventObjModelGeneratorCls(service,
                                                        event,
                                                        api_call_ast_node,
                                                        interm_interf_record_set)
        ast_node = ast.Assign(targets=[ast.Name(id="event", ctx=ast.Store())],
                              value=event_obj_model_gen.get_event_obj_model())
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
        try:
            for i, child in enumerate(body[:]):
                self.__api_to_process = None
                # The method pre_Call is automatically called when the
                # method walk, provided by the base class, is executed.
                self.walk(child)
                if self.__api_to_process is not None:
                    for event_obj_init_stmt, syn_handler_call in self._get_syn_code(self.interf_record.service,
                                                                                    self.interf_record.instance_type,
                                                                                    self.__api_to_process,
                                                                                    self.interm_interf_record_set):
                        if all([event_obj_init_stmt is not None, syn_handler_call is not None]):
                            # Inject synthesized code with initialization of event object
                            body.insert(i + counter, event_obj_init_stmt)
                            # Increment auxiliary counter
                            counter += 1
                            # Inject synthesized code with handler call
                            body.insert(i + counter, syn_handler_call)
                            # Increment auxiliary counter
                            counter += 1
        except Exception as e:
            print(f'--- WARNING: AST node of type {type(body)} not processed - Details: ---')
            print(f'--- {e} ---')
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
                                               self.cur_node,
                                               self.cur_node.func.attr,
                                               self.api_lineno_func_name_dict[self.cur_node.lineno]):
                    # Store AST node with API call
                    self.__api_to_process = self.cur_node
                else:
                    print(f'--- Permissions for API {self.cur_node.func.attr} not found - No code injected ---')
        except AttributeError:
            # This exception is raised every time the func attribute of
            # the of Call object is not an Attribute object. To avoid
            # noisy log files, no message is printed in this case.
            pass 
        except Exception as e:
            print('--- Exception raised during code synthesis and injection - Details: ---')
            print(f'--- {e} ---')
        return True

class IntermInterfaceRecordCls(NamedTuple):
    line_no: int
    instance_name: Optional[str]
    ast_node: ast.Call
