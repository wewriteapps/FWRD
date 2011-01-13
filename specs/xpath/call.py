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

def set_test():
    return set(['a','a','b','b','c','c','c'])

def object_test(*args, **kwargs):
    o = PlainObject()
    o.spam = 'eggs'
    return o

def raising_test():
    raise Exception('this is an exception')

def arg_test(spam):
    return spam

def noarg_test():
    return None

def list_dicts_test():
    return [{'foo': 'bar'}, {'a': 'b', 'c': 'd'}]
