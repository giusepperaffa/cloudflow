# ========================================
# Import Python Modules (Standard Library)
# ========================================
import json
import os

# =========
# Functions
# =========
def extract_dict_from_json(folder_full_path, json_file):
    """
    Function that maps a JSON file into a dictionary.
    The file extension must be .json. If an exception
    is raised, an empty dictionary is returned. 
    """
    try:
        # Function output initialization
        extracted_dict = dict()
        assert os.path.splitext(json_file)[1] == '.json', 'Exception raised - JSON file with incorrect extension'
        with open(os.path.join(folder_full_path, json_file), mode='r') as file_obj:
            extracted_dict = json.load(file_obj)
    except AssertionError as e:
        print(f'--- {e} ---')
    except Exception as e:
        print(f'--- Exception raised while processing the JSON file {json_file} - Details: ---')
        print(f'--- {e} ---')
    return extracted_dict
 