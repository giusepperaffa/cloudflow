# ========================================
# Import Python Modules (Standard Library)
# ========================================
import argparse

# ========================================
# Import Python Modules (Project Specific)
# ========================================
from cloudflow.modules.analysisreslib import AnalysisManagerCls

# =========
# Functions
# =========
def process_program_inputs():
    parser_obj = argparse.ArgumentParser(description='Tool to perform data flow \
        analysis of serverless applications')
    mode_group_parser_obj = parser_obj.add_mutually_exclusive_group(required=True)
    mode_group_parser_obj.add_argument('-s', '--single', action='store', type=str, metavar='full_path', \
        help='Single Mode - Only the specified repository is analysed')
    mode_group_parser_obj.add_argument('-m', '--multi', action='store', type=str, metavar='full_path', \
        help='Multiple Mode - All the repositories within the specified folder are analysed')
    mode_group_parser_obj.add_argument('-mb', '--microbenchmarks', action='store', type=str, metavar='category', \
        help='Microbenchmarks Mode - The repositories within the microbenchmarks suite are analysed',
        choices=['all', 'inter-procedural', 'intra-procedural', 'simple-apps'])
    mode_group_parser_obj.add_argument('-lp', '--log-processing', action='store_true', \
        help='Log Processing Mode - Starts processing of tool log file')
    config_group_parser_obj = parser_obj.add_mutually_exclusive_group(required=False)
    config_group_parser_obj.add_argument('-cf', '--config-file', action='store', type=str, metavar='config_file', \
        help='Configuration File - Configuration file name (optional)')
    return parser_obj.parse_args()

def main():
    # Create instance of AnalysisManagerCls class
    analysis_manager = AnalysisManagerCls(process_program_inputs())
    # Start analysis with dedicated method
    analysis_manager.perform_analysis()
