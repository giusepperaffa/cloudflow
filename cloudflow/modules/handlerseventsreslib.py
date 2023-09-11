# ========================================
# Import Python Modules (Standard Library)
# ========================================
import collections
import re

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.utils.customprintreslib import print_table

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

    # === Protect Method ===
    def _postprocess_extr_event_info(self, extr_event_info):
        """
        Method that further postprocesses the extracted event information
        data structure to deal with special cases (i.e., ad-hoc processing).
        """
        postproc_extr_event_info = list()
        for extr_event in extr_event_info:
            if extr_event == ('stream', 'dynamodb'):
                # In this special dynamodb-related case, the
                # elements of the extracted tuple are swapped.
                postproc_extr_event_info.append((extr_event[1], extr_event[0]))
            else:
                postproc_extr_event_info.append(extr_event)
        return postproc_extr_event_info

    # === Protect Method ===
    def _get_event_dict_info(self, event_dict):
        """
        Method processing the event dictionary extracted for a specific handler.
        It returns a list of tuples, each specifying a service and an event.
        """
        extr_events_info = []
        for service, info in event_dict.items():
            if isinstance(info, dict):
                for flt_key in (key for key in info if key in ('method', 'event', 'type')):
                    try:
                        # The split string method takes an integer as input argument
                        # that specifies the occurrence where the split has to take
                        # place (the other occurrences are ignored). In the following
                        # statement, the split method identifies the service-related
                        # information, which is then removed.
                        extr_events_info.append((service, info[flt_key].split(':', 1)[1]))
                    except IndexError:
                        extr_events_info.append((service, info[flt_key]))
            elif isinstance(info, str):
                extr_events_info.append((service, info))
            else:
                print('--- No information extracted - Data structure not supported ---')
        return self._postprocess_extr_event_info(extr_events_info)

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
                            self.handlers_dict[handler].update(self._get_event_dict_info(event_dict))
                    except KeyError as e:
                        print(f'--- Handler {handler} - Key {e} not found ---')
                    except Exception as e:
                        print(f'--- Events of handler {handler} not extracted ---')
                        print('--- Extracted data structure might not be supported - Details: ---')
                        print(f'--- {e} ---')
                else:
                    print(f'--- Information about handler {handler} is invalid ---')
                    print('--- Check that the handler is correctly specified ---')
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

    # === Method ===
    def pretty_print_handlers_dict(self):
        table_contents = [[handler, ' / '.join(re.sub(r"[\(\)']", '', str(elem).replace(', ', ' => ')) \
            for elem in event_set)] for handler, event_set in sorted(self.handlers_dict.items())]
        print_table(table_contents, ['Handlers', 'Events'])
