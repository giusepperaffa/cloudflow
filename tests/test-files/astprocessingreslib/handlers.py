def my_func(input):
    print('I am a module-level function')

def my_func_with_nested_func(input):
    # Nested function
    def my_func(input):
        print('I am a nested function')

class MyCls:
    # Method with same name as module-level function
    def my_func(self):
        print('I am class method')

