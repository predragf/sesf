def print_enter_exit_decorator(decorated_function):
    def wrapper(*args, **kwards):
        print("-----------Entering: {0}-----------".format(decorated_function.__name__))
        decorated_function_result = decorated_function(*args, **kwards)
        print("-----------Exiting: {0}-----------".format(decorated_function.__name__))
        return decorated_function_result
    return wrapper
