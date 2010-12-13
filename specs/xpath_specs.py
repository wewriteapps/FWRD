import os
import re
import sys
import unittest

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import XPathCallbacks


class XpathSpec(unittest.TestCase):
    """NOT IMPLEMENTED: XPath Spec"""

    def setUp(self):
        self.xpath = XPathCallbacks()

    def it_should_get_parameters(self):
        pass

    def it_should_get_session(self):
        pass

    def it_should_get_environ(self):
        pass

    def it_should_format_a_title(self):
        pass

    def it_should_format_to_lower(self):
        pass

    def it_should_format_to_upper(self):
        pass

    def it_should_strip_whitespace(self):
        pass

    def it_should_coalesce_values(self):
        pass

    def it_should_join_values_into_a_string(self):
        pass

    def it_should_format_a_date(self):
        pass

    def it_should_format_a_time(self):
        pass

    def it_should_recognise_empty_values(self):
        pass

    def it_should_return_a_range(self):
        pass

    def it_should_return_a_range_as_nodes(self):
        pass

    def it_should_unescape_xml_entities(self):
        pass
