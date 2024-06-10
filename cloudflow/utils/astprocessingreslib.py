# =========
# Functions
# =========
def get_call_input_ast_node(call_ast_node, input_id, input_pos_arg=None):
    """
    Function that processes an AST node of type Call to
    obtain the AST node of the Call input specified by
    input_id. If the latter identifier is not among the
    Call keywords arguments, the position input_pos_arg
    is used instead. Function input arguments:
    -) call_ast_node: AST node of type ast.Call.
    -) input_id: String specifying the input argument
    of the processed AST Call node.
    -) input_pos_arg: Integer or string specifying the
    position of the input argument of the processed AST
    Call node. Default value: None.
    If the processing fails, e.g., the specified input
    argument of the AST Call node is not found, the
    function returns None.  
    """
    # Retrieve the AST node of the specified input argument
    if input_id in [keyword.arg for keyword in call_ast_node.keywords]:
        # --------------------------------------------------------
        # CASE 1 - The AST node of the specified input argument is
        # retrieved from the AST Call node keyword arguments.
        # --------------------------------------------------------
        input_ast_node = [keyword.value for keyword
                          in call_ast_node.keywords if keyword.arg == input_id][0]
    else:
        # --------------------------------------------------------
        # CASE 2 - The AST node of the specified input argument is
        # retrieved from the API Call node positional arguments.
        # --------------------------------------------------------
        try:
            input_ast_node = call_ast_node.args[int(input_pos_arg)]
        except:
            print(f'--- WARNING: No information extracted for {input_id} ---')
            # Return None, as no AST node was extracted from AST Call node  
            return
    # Return extracted AST node
    return input_ast_node
