def foo():
    pass

def bar(*args, **kwargs):
    return args, kwargs

def basic_filter(message):
    def wrapper(func):
        def wrapped(*args, **kwargs):
            return (message, func(*args, **kwargs))
        return wrapped
    return wrapper
