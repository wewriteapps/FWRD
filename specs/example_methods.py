def foo():
    pass

def bar(*args, **kwargs):
    return args, kwargs

def basic_filter(message):
    def wrapper(func):
        def wrapped(*args, **kwargs):
            print message
            return func(*args, **kwargs)
        return wrapped
    return wrapper
