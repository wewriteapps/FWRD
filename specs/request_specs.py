import os
import re
import sys
import unittest

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import Request

class RequestEnvironSpec(unittest.TestCase):

    def setUp(self):
        pass

class Request

class GetRequestSpec(unittest.TestCase):

    def setUp(self):
        self.request = Request()

    def it_should_parse_file_extensions_correctly(self):
        pass

    def it_should_parse_get_params_correctly(self):
        pass


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
