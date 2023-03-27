# --------
# Fuctions
# --------
def print_table(data_struct, column_headings=None, column_width_margin=2):
    """
    DESCRIPTION: This function prints out a table starting from the following types
    of data structures:
    a) List of lists (nested lists contain information to be displayed in a table row).
    b) Tuple of tuples (nested tuples contain information to be displayed in a table row).
    The User can also specify the column headings and a margin that is used to increase
    the width of the table columns (to improve readability). The code relies on the fact
    that all the elements in the input argument data_struct have the same number of
    sub-elements.
    SYNTAX: print_table(data_struct, column_headings=None,  column_width_margin=2)
    where:
    1) data_struct: List of lists / Tuple of tuples. Nested lists / tuple contain
    information to be displayed in a table row.
    2) column_headings: List of strings specifying the column headings. If the default
    value for this argument is used, default strings will be printed as headings (Colum 1,
    Colum 2, and so on). Defaul value: None.
    3) column_width_margin: Integer used to increase the width of the table columns (to
    improve readability). Default value: 2.
    """
    try:
        # When the column_headings input argument has its default value, it is initialized
        # by using default strings with the following list comprehension.
        if column_headings is None:
            column_headings = ['Column ' + str(index) for index in range(len(data_struct[0]))]
        # The column widths are calculated and then stored in a dictionary.
        column_width_dict = dict((column_heading_index, max(max(len(str(elem[column_heading_index])) for elem in data_struct), \
            len(column_heading))) for column_heading_index, column_heading in enumerate(column_headings))
        # Print blank line to improve readability.
        print()
        # Print Table Heading
        table_heading = '|' + ''.join(column_heading.center(column_width_dict[column_heading_index] + column_width_margin) + '|' \
            for column_heading_index, column_heading in enumerate(column_headings))
        print('=' * len(table_heading))
        print(table_heading)
        print('=' * len(table_heading))
        # Print Table Content
        for nested_data_struct in data_struct:
            table_row = '|' + ''.join([str(nested_elem).center(column_width_dict[nested_elem_index] + column_width_margin) + '|' \
                for nested_elem_index, nested_elem in enumerate(nested_data_struct)])
            print(table_row)
            print('-' * len(table_row))
        else:
            # Print blank line to improve readability.
            print()
    except IndexError as e:
        print('--- Exception raised (IndexError) while printing a table - Details: ---')
        print(f'--- {e} ---')
        print('--- Check the contents of the passed data structures ---')
    except Exception as e:
        print('--- Exception raised while printing a table - Details: ---')
        print(f'--- {e} ---')

