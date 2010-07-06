import os
import re
import sys
import unittest

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import Request

class Environ(object):
    __slots__ = [
        'params',
        ]
    def __init__(self, **kwargs):
        self.params = {}
        self.params['PATH_INFO'] = ''
        self.params['REQUEST_METHOD'] = 'GET'
        self.params['QUERY_STRING'] = ''

        for key, value in kwargs.iteritems():
            self.params[key.upper()] = value

    def __getitem__(self, name):
        return self.params.get(name, '')

class ServerTest(unittest.TestCase):
    pass

class RequestEnvironSpec(unittest.TestCase):

    def setUp(self):
        pass

"""
class Request(unittest.TestCase):

    def setUp(self):
        pass
"""

class GetRequestSpec(unittest.TestCase):

    def setUp(self):
        self.request = Request(Environ(path_info='/foo/bar/baz?a=1&b[]=2&b[]=3&baz=true'))

    def it_should_parse_file_extensions_correctly(self):
        self.request = Request(Environ(path_info='/foo/bar.baz'))
        self.assertEqual('baz', self.request.path[1])

        self.request = Request(Environ(path_info='/foo.bar/boz.baz'))
        self.assertEqual('baz', self.request.path[1])

    def it_should_parse_get_params_correctly(self):
        print self.request['GET']
        for key in ['a','b','baz']:
            self.assert_(key in self.request['GET'])


class PostRequestSpec(unittest.TestCase):

    def setUp(self):
        pass

    def it_should_parse_post_params_correctly(self):
        pass

    def it_should_parse_multipart_posts_correctly(self):
        pass

    def ensure_get_does_not_clobber_post_params(self):
        pass

    def it_should_not_allow_incorrect_content_length(self):
        pass
