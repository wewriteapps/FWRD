import os
import re
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import HeaderContainer

class HeaderSpec(unittest.TestCase):

    def setUp(self):
        self.headers = HeaderContainer()

    def it_should_accept_params_at_init(self):
        obj = HeaderContainer(content_type='text/xml')

        self.assertEqual(
            str(obj),
            'Content-Type: text/xml\r\n\r\n'
            )

        obj = HeaderContainer(
            content_type='text/plain',
            pragma='no-cache',
            expires='Thu, 01 Dec 1994 16:00:00 GMT'
            )

        self.assertEqual(
            str(obj),
            'Expires: Thu, 01 Dec 1994 16:00:00 GMT\r\nContent-Type: text/plain\r\nPragma: no-cache\r\n\r\n'
            )

    def it_should_accept_headers(self):
        self.headers.add_header('content-type', 'text/xml')

        self.assertEqual(
            str(self.headers),
            'Content-Type: text/xml\r\n\r\n'
            )

    def it_should_delete_specific_headers(self):
        self.headers = HeaderContainer(
            content_type='text/plain',
            pragma='no-cache',
            expires='Thu, 01 Dec 1994 16:00:00 GMT'
            )

        self.assertEqual(
            str(self.headers),
            'Expires: Thu, 01 Dec 1994 16:00:00 GMT\r\nContent-Type: text/plain\r\nPragma: no-cache\r\n\r\n'
            )

        del self.headers['expires']

        self.assertEqual(
            str(self.headers),
            'Content-Type: text/plain\r\nPragma: no-cache\r\n\r\n'
            )

        self.headers.drop('pragma')

        self.assertEqual(
            str(self.headers),
            'Content-Type: text/plain\r\n\r\n'
            )

    def it_should_clear_all_headers(self):
        self.headers.add_header('content-type', 'text/xml')

        self.assertEqual(
            str(self.headers),
            'Content-Type: text/xml\r\n\r\n'
            )

        self.headers.clear()

        self.assertEqual(
            str(self.headers),
            '\r\n'
            )

    def it_should_allow_multiple_headers(self):
        self.headers.add_header('warning', 'First Warning')
        self.headers.add_header('warning', 'Second Warning')
        self.headers.add_header('warning', 'Third Warning')

        self.assertEqual(
            self.headers.get('warning'),
            'First Warning'
            )

        self.assertEqual(
            self.headers['warning'],
            'First Warning'
            )

        self.assertEqual(
            self.headers.get_all('warning'),
            ['First Warning', 'Second Warning', 'Third Warning']
            )

        self.assertEqual(
            str(self.headers),
            'Warning: First Warning\r\nWarning: Second Warning\r\nWarning: Third Warning\r\n\r\n'
            )

    def it_should_show_correct_length(self):
        self.headers.add_header('content-type', 'text/xml')
        self.headers.add_header('warning', 'First Warning')
        self.headers.add_header('warning', 'Second Warning')
        self.headers.add_header('warning', 'Third Warning')

        self.assertEqual(
            len(self.headers),
            2
            )
