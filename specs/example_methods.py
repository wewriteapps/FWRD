def foo():
    pass

def bar(*args, **kwargs):
    return args, kwargs

def spam(eggs):
    pass

def basic_filter(message):
    def wrapper(func):
        def wrapped(*args, **kwargs):
            return (message, func(*args, **kwargs))
        return wrapped
    return wrapper

def hello_filter(func):
    def wrapped(*args, **kwargs):
        return ("hello", func(*args, **kwargs))
    return wrapped

def world_filter(func):
    def wrapped(*args, **kwargs):
        return ("world", func(*args, **kwargs))
    return wrapped


class Bar(object):
    def bar(self, id):
        pass
