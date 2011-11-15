import os
import re
import sys
import unittest

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from http_spec import WSGITestBase

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import *


class RequestCookieSpec(WSGITestBase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.app.reset()
        self.app.config.format['xsl'] = {
            'stylesheet': 'request_cookie_spec.xsl',
            }
        self.app.router.clear()

    def it_should_parse_cookies_correctly(self):
        self.app.router.add('/request_cookie', None)
        self.make_request('/request_cookie', env={'HTTP_COOKIE': 'spam=eggs; foo=bar'})
        self.assertEqual(self.app.request.COOKIES, {'spam': 'eggs', 'foo': 'bar'})


class ResponseCookieSpec(WSGITestBase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.app.reset()
        self.app.config.format['xsl'] = {
            'stylesheet': 'request_cookie_spec.xsl',
            }
        self.app.router.clear()

    def it_should_set_cookies_correctly(self):
        def request_cookie_test():
            response.set_cookie('spam', 'eggs')
        self.app.router.add('/response_cookie', request_cookie_test)
        self.assertHeader('Set-Cookie', 'spam=eggs', route='/response_cookie')

    def it_should_set_multiple_cookies_correctly(self):
        def request_multiple_cookie_test():
            response.set_cookie('spam', 1)
            response.set_cookie('eggs', 2)
        self.app.router.add('/response_multi_cookie', request_multiple_cookie_test)

        self.make_request('/response_multi_cookie')
        print self.app.response.cookies
        
        self.assertInHeader('Set-Cookie', 'spam=1', route='/response_multi_cookie')
        self.assertInHeader('Set-Cookie', 'eggs=2', route='/response_multi_cookie')

    def it_should_set_cookie_expiry(self):
        self.skipTest('')

    def it_should_fail_for_invalid_expiry(self):
        self.skipTest('')

    def it_should_set_cookie_max_age(self):
        """it should set cookie max-age"""
        self.skipTest('')

    def it_should_fail_for_invalid_max_age(self):
        """it should faile for invalid max-age"""
        self.skipTest('')

    def it_should_set_cookie_path(self):
        self.skipTest('')

    def it_should_fail_for_invalid_path(self):
        self.skipTest('')

    def it_should_set_cookie_domain(self):
        self.skipTest('')

    def it_should_set_secure_flag(self):
        self.skipTest('')

    def it_should_set_httponly_flag(self):
        self.skipTest('')

    def it_should_fail_for_invalid_values(self):
        self.skipTest('')

    def it_should_fail_when_setting_a_large_value(self):
        self.skipTest('')

    
