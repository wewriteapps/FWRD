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

from FWRD import Request, ResponseParameterError


class RequestCookieSpec(WSGITestBase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.app.reset()
        self.app.config.format['xsl'] = {
            'stylesheet': 'request_cookie_spec.xsl',
            }
        self.app.router.clear()

    def it_should_parse_cookies_correctly(self):
        self.app.router.add('/foo', None)
        self.make_request('/foo', env={'HTTP_COOKIE': 'spam=eggs; foo=bar'})
        self.assertEqual(self.app.request.COOKIES, {'spam': 'eggs', 'foo': 'bar'})

