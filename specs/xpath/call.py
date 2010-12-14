class PlainObject(object):
    pass

def string_test(*args, **kwargs):
    return "spam"

def list_test(*args, **kwargs):
    return ['spam','eggs']

def tuple_test(*args, **kwargs):
    return ('spam', 'eggs')

def dict_test(*args, **kwargs):
    return {'spam': 'eggs'}

def object_test(*args, **kwargs):
    o = PlainObject()
    o.spam = 'eggs'
    return o

def arg_test(spam):
    return spam

def noarg_test():
    return None
