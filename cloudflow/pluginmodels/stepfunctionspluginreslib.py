# ========================================
# Import Python Modules (Standard Library)
# ========================================
import collections
import re

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.pluginmodels.pluginmodelssharedreslib import PluginModelCls 

# =======
# Classes
# =======
class StepFunctionsPluginModelCls(PluginModelCls):
    # === Constructor ===
    def __init__(self, config_dict):
        """
        Class constructor. It expects to receive a dictionary that maps
        the Serverless Framework YAML configuration file.
        """
        # Attribute initialization
        self.config_dict = config_dict

    # === Protected Method ===
    def _process_state_machine_definition(self, state_machine_dict):
        """
        Method that processes a state machine dictionary
        to extract its handlers, which are stored as
        strings and then returned in a list.
        NOTE: Only handlers that match those specified
        under the 'functions' tag of the YAML file are
        considered valid.
        """
        # Initialize list returned by the method
        extr_handlers_list = list()
        try: 
            for state in state_machine_dict['definition']['States']:
                print(f'--- Processing state: {state}... ---')
                state_dict = state_machine_dict['definition']['States'][state]
                # NOTE: The following regular expression, which extracts
                # the name of the handler from the Resource tag, relies
                # on the convention used by the Serverless Framework to
                # identify deployed handlers.
                extr_handler_reg_exp = re.compile('-([\w]+)$')
                extr_handler = extr_handler_reg_exp.search(state_dict['Resource']).group(1)
                # The handler extracted from the state machine definition
                # is included in returned list ONLY if it matches one of
                # the handlers specified under the 'functions' tag of the
                # YAML file.  
                if extr_handler in self.config_dict['functions']:
                    extr_handlers_list.append(extr_handler)
        except KeyError as e:
            print(f'--- Exception raised - Key {e} not found ---')
        except Exception as e:
            print('--- Exception raised - Details: ---')
            print(f'--- {e} ---')
        return extr_handlers_list

    # === Method ===
    def extract_events(self):
        """
        Method that extracts event-related, plugin-specific
        information and returns a dictionary structured as
        follows:
        -) Keys: Handlers specified as strings. These are
        the handlers triggered through the plugin-specific
        functionality.
        -) Values: Sets including two-element tuples. The
        first element specifies the service, whilst the
        second specifies the event.
        """
        # Initialize data structure returned by the method
        event_info_dict = collections.defaultdict(set)
        # The following cycle processes the state machines that
        # implement the step function. For further information:
        # https://www.serverless.com/plugins/serverless-step-functions 
        try:
            for state_machine in self.config_dict['stepFunctions']['stateMachines']:
                print(f'--- Processing step function state machine: {state_machine} ---')
                state_machine_dict = self.config_dict['stepFunctions']['stateMachines'][state_machine]
                if 'events' in state_machine_dict:
                    for event_dict in state_machine_dict['events']:
                        # APPROXIMATION: This implementation assumes that all
                        # the handlers identified within the state machine are
                        # triggered by the event being processed.
                        service = list(event_dict.keys())[0] 
                        # NOTE: Only events specified via the 'method' tag in
                        # the YAML file are currently supported. 
                        for handler in self._process_state_machine_definition(state_machine_dict):
                            event_info_dict[handler].add((service, event_dict[service]['method']))
                else:
                    print(f'--- No event-related information found within state machine {state_machine} ---')
                    print('--- Check that the state machine is correctly specified ---')
        except KeyError as e:
            print(f'--- Exception raised - Key {e} not found ---')
        except Exception as e:
            print(f'--- Exception raised while processing state machine {state_machine} - Details: ---')
            print(f'--- {e} ---')
        return event_info_dict
