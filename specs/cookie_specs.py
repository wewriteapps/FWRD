import os
import re
import sys
import time
import unittest

from datetime import datetime, timedelta

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

        self.assertInHeader('Set-Cookie', 'spam=1', route='/response_multi_cookie')
        self.assertInHeader('Set-Cookie', 'eggs=2', route='/response_multi_cookie')

    def it_should_set_cookie_expiry_from_int(self):
        expires = 3600
        expires_dt = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(expires))
        def request_cookie_expires():
            response.set_cookie('a', 1, expires=expires)
        self.app.router.add('/response_cookie_expires_int', request_cookie_expires)

        self.assertHeader('Set-Cookie',
                          'a=1; expires=%s' % expires_dt,
                          route='/response_cookie_expires_int')

    def it_should_set_cookie_expiry_from_float(self):
        expires = 3600.01 * 2
        expires_dt = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(expires))
        def request_cookie_expires():
            response.set_cookie('a', 1, expires=expires)
        self.app.router.add('/response_cookie_expires_float', request_cookie_expires)

        self.assertHeader('Set-Cookie',
                          'a=1; expires=%s' % expires_dt,
                          route='/response_cookie_expires_float')

    def it_should_set_cookie_expiry_from_datetime(self):
        expires = datetime.utcnow() + timedelta(hours=3)
        expires_dt = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
        def request_cookie_expires():
            response.set_cookie('a', 1, expires=expires)
        self.app.router.add('/response_cookie_expires_dt', request_cookie_expires)

        self.assertHeader('Set-Cookie',
                          'a=1; expires=%s' % expires_dt,
                          route='/response_cookie_expires_dt')

    def it_should_fail_for_string_as_expiry(self):
        def response_cookie_invalid_value_str():
            response.set_cookie('a', 1, expires='tomorrow')

        self.app.router.add('/response_cookie_expires_invalid',
                            response_cookie_invalid_value_str)
        self.assertRaises(TypeError,
                          self.make_request,
                          '/response_cookie_expires_invalid')

    def it_should_fail_for_none_as_expiry(self):
        def response_cookie_invalid_value_none():
            response.set_cookie('a', 1, expires=None)

        self.app.router.add('/response_cookie_expires_invalid',
                            response_cookie_invalid_value_none)
        self.assertRaises(TypeError,
                          self.make_request,
                          '/response_cookie_expires_invalid')

    def it_should_fail_for_true_as_expiry(self):
        def response_cookie_invalid_value_true():
            response.set_cookie('a', 1, expires=True)

        self.app.router.add('/response_cookie_expires_invalid',
                            response_cookie_invalid_value_true)
        self.assertRaises(TypeError,
                          self.make_request,
                          '/response_cookie_expires_invalid')

    def it_should_fail_for_false_as_expiry(self):
        def response_cookie_invalid_value_false():
            response.set_cookie('a', 1, expires=False)

        self.app.router.add('/response_cookie_expires_invalid',
                            response_cookie_invalid_value_false)
        self.assertRaises(TypeError,
                          self.make_request,
                          '/response_cookie_expires_invalid')

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

    
