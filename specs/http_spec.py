import os
import re
import sys
import unittest
import wsgiref
import wsgiref.util
import wsgiref.validate

try:
    from cStringIO import StringIO 
except ImportError:
    from StringIO import StringIO

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import *

class DummyInputWrapper(object):
    def __init__(self, value):
        self.value = value

    def read(self, *args):
        return self.value

    readline = readlines = __iter__ = read

class WSGITestBase(unittest.TestCase):

    def setUp(self):
        self.config = config
        self.app = application
        self.config.port = 9090
        self.wsgiapp = wsgiref.validate.validator(self.app)

    def make_request(self, path, method='GET', qs='', env={}):
        result = {
            'code': 0,
            'status': 'empty',
            'headers': {},
            'body': '',
            }

        def start_response(status, header):
            result['code'], result['status'] = status.split()
            for name, value in header:
                name = name.title()
                if name in result['headers']:
                    result['headers'][name] += ', '+value
                else:
                    result['headers'][name] = value

        env = self.make_env(env, path=path, method=method, qs=qs)

        response = self.wsgiapp(env, start_response)

        try:
            response.close()
        except AttributeError:
            pass
        finally:
            del response

        result['code'] = int(result['code'])
        return result

    def make_multipart_request(self, path, method='POST', qs='', env={}, body=''):
        raise NotImplementedError()

    def make_env(self, env={}, path='/', method='GET', qs=''):
        wsgiref.util.setup_testing_defaults(env)
        method = method.upper().strip()

        env['REQUEST_METHOD'] = method
        env['PATH_INFO'] = path

        if method == 'GET':
            env['QUERY_STRING'] = qs

        elif method == 'POST':
            env['QUERY_STRING'] = ''
            env['CONTENT_LENGTH'] = str(len(qs))
            env['wsgi.input'] = StringIO(qs)

        else:
            raise NotImplementedError('%s testing not yet implemented' % method)

        return env

    def get_callable(self, multipart=False):
        if multipart:
            return self.make_multipart_request

        return self.make_request
        
    def assertStatus(self, code, route='/', multipart=False, **kwargs):
        self.assertEqual(code, self.get_callable(multipart)(route, **kwargs)['code'])

    def assertBody(self, body, route='/', multipart=False, **kwargs):
        self.assertEqual(body, self.get_callable(multipart)(route, **kwargs)['body'])

    def assertHeader(self, name, value, route='/', multipart=False, **kwargs):
        self.assertEqual(value, self.get_callable(multipart)(route, **kwargs)['headers'].get(name))

    def assertInHeader(self, name, value, route='/', multipart=False, **kwargs):
        self.assert_(value in self.get_callable(multipart)(route, **kwargs)['headers'].get_all(name))



