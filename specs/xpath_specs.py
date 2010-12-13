import os
import re
import sys
import unittest

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import ResponseFactory, XPathCallbacks
from response_specs import ResponseBaseSpec, PlainObject, ComplexObject

class XpathSpec(ResponseBaseSpec):
    """NOT IMPLEMENTED: XPath Spec"""

    def setUp(self):
        self.request = PlainObject()
        self.request.path = ('/', '/', '')
        self.request.route = '/'
        self.request.method = 'GET'
        self.response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='specs',
            default_stylesheet='xpath_methods_spec.xsl'
            )

        #self.xpath = XPathCallbacks()

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

    def it_should_call_a_method_successfully(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='specs/xpath',
            default_stylesheet='call_method.xsl'
            ).format()

        expected = ''.join([
            """<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Call-Method Spec</title></head><body>""",
            """<h1>Simple Calls</h1><dl>""",
            """<dt>String</dt>""",
            """<dd><result>spam</result></dd>""",
            """<dd>spam</dd>""",
            """<dt>List</dt>""",
            """<dd><result nodetype="list"><i>spam</i><i>eggs</i></result></dd>""",
            """<dd>spam</dd>""",
            """<dd>eggs</dd>""",
            """<dt>Tuple</dt>""",
            """<dd><result nodetype="fixed-list"><i>spam</i><i>eggs</i></result></dd>""",
            """<dd>spam</dd>""",
            """<dd>eggs</dd>""",
            """<dt>Dict</dt>""",
            """<dd><result><spam>eggs</spam></result></dd>""",
            """<dd>eggs</dd>"""
            """</dl></body></html>"""])

        self.assertEqual(response, expected)
