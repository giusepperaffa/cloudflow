# ========================================
# Import Python Modules (Standard Library)
# ========================================
import collections
import yaml
import sys

# =======
# Classes
# =======
class HandlersEventsIdentifierCls:
    # === Constructor ===
    def __init__(self, config_dict):
        """
        Class constructor. It expects to receive a dictionary that maps
        the Serverless Framework YAML configuration file.
        """
        self.config_dict = config_dict
        # Data structure containing handlers-related information
        # extracted by the methods implemented in this class.
        self.handlers_dict = collections.defaultdict(set)
        self.extract_info_from_functions()

    # === Method ===
    def extract_info_from_functions(self):
        """
        Method extracting handlers and events-related information from
        functions entry.
        """
        try:
            extr_handlers_dict_info = self.config_dict['functions']
            # Process and validate handler-specific entries
            for handler in extr_handlers_dict_info:
                # If a handler entry is not found, the information in the
                # configuration file is incomplete and it will not be processed
                if 'handler' in extr_handlers_dict_info[handler]:
                    self.handlers_dict[handler] = set()
                    # Start extraction of information about events
                    try:
                        for event_dict in extr_handlers_dict_info[handler]['events']:
                            # NOTE: With the following statement, if a handler is
                            # triggered by multiple events associated with certain
                            # service, e.g., the event will be counted only once
                            self.handlers_dict[handler].update(event_dict.keys())
                    except KeyError as e:
                        print(f'--- Handler {handler} - Key {e} not found ---')
                    except Exception as e:
                        print(f'--- Events of handler {handler} not extracted ---')
                        print('--- Extracted data structure might not be supported - Details: ---')
                        print(f'--- {e} ---')
                else:
                    print(f'--- Information about handler {handler} is invalid ---')
                    print('--- Check that a handler is correctly specified ---')
        except KeyError as e:
            print(f'--- Exception raised - Key {e} not found ---')
        except Exception as e:
            print(f'--- Exception raised while processing handler {handler} - Details ---')
            print(f'--- {e} ---')

    # === Method ===
    def get_num_of_events(self):
        return sum(len(self.handlers_dict[handler]) for handler in self.handlers_dict)

    # === Method ===
    def get_num_of_handlers(self):
        return len(self.handlers_dict)
