import os
import re
import sys
import unittest

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import ResponseFactory, XPathFunctions
from response_specs import ResponseBaseSpec, PlainObject, ComplexObject

class XpathSpec(ResponseBaseSpec):
    """XPath Spec"""

    def setUp(self):
        self.request = PlainObject()
        self.request.path = ('/', '/', '')
        self.request.route = '/'
        self.request.method = 'GET'
        self.response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='.',
            default_stylesheet='xpath_methods_spec.xsl'
            )

        #self.xpath = XPathCallbacks()

    """
    def it_should_get_parameters(self):
        pass

    def it_should_get_session(self):
        pass

    def it_should_get_environ(self):
        pass

    def it_should_format_get_params(self):
        '''it should format GET params'''
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='xpath',
            default_stylesheet='get_params.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Format Title</title></head><body>Format Title</body></html>')
    """

    def it_should_format_a_title(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='xpath',
            default_stylesheet='title.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Format Title</title></head><body>Format Title</body></html>')

    def it_should_format_to_lower(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='xpath',
            default_stylesheet='lower.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Lower-Case</title></head><body>lower-case</body></html>')

    def it_should_format_to_upper(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='xpath',
            default_stylesheet='upper.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Upper-Case</title></head><body>UPPER-CASE</body></html>')

    def it_should_strip_whitespace(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='xpath',
            default_stylesheet='whitespace.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Strip Whitespace</title></head><body>"whitespace"</body></html>')

    def it_should_coalesce_values(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='xpath',
            default_stylesheet='coalesce.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Coalesce</title></head><body>true</body></html>')

    def it_should_join_values_into_a_string(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='xpath',
            default_stylesheet='join.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Join</title></head><body>this-is-a-test</body></html>')

    def it_should_format_a_date(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='xpath',
            default_stylesheet='date.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Format a Date</title></head><body>Jan  1, 2010</body></html>')

    def it_should_format_a_time(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='xpath',
            default_stylesheet='time.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Format a Time</title></head><body>Jan  1, 2010</body></html>')

    def it_should_recognise_empty_values(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='xpath',
            default_stylesheet='empty.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Empty Tests</title></head><body><ul><li>true</li><li>true</li><li>true</li><li>true</li></ul></body></html>')

    def it_should_return_a_range(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='xpath',
            default_stylesheet='range.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Range</title></head><body>0,1,2,3,4</body></html>')

    def it_should_return_a_range_as_nodes(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='xpath',
            default_stylesheet='range_as_nodes.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Range of Nodes</title></head><body><items><item>0</item><item>1</item><item>2</item><item>3</item><item>4</item></items></body></html>')

    def it_should_unescape_xml_entities(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='xpath',
            default_stylesheet='xml_entities.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>XML Entities</title></head><body><input value="&gt;&amp;&lt;"/></body></html>')

    def it_should_call_a_method_successfully(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='xpath',
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
            """<dt>Set</dt>""",
            """<dd><result nodetype="unique-list"><i>a</i><i>c</i><i>b</i></result></dd>""",
            """<dd>a</dd>""",
            """<dd>c</dd>""",
            """<dt>Tuple</dt>""",
            """<dd><result nodetype="fixed-list"><i>spam</i><i>eggs</i></result></dd>""",
            """<dd>spam</dd>""",
            """<dd>eggs</dd>""",
            """<dt>Dict</dt>""",
            """<dd><result><spam>eggs</spam></result></dd>""",
            """<dd>eggs</dd>"""
            """<dt>List of Dicts</dt>""",
            """<dd><result nodetype="list"><i><foo>bar</foo></i><i><a>b</a><c>d</c></i></result></dd>""",
            """<dt>Object</dt>""",
            """<dd><result><PlainObject nodetype="container"><spam>eggs</spam></PlainObject></result></dd>""",
            """<dd>eggs</dd>""",
            """<dt>Exception</dt>""",
            """<dd><message>this is an exception</message></dd>""",
            """</dl>""",
            """<h1>Advanced Calls</h1>""",
            """<dl>""",
            """<dt>Accepts Args</dt>""",
            """<dd>eggs</dd>""",
            """<dt>No Args</dt>""",
            """<dd>noarg_test() takes no arguments (1 given)</dd>""",
            """</dl>""",
            """</body></html>"""])

        self.assertEqual(response, expected)
