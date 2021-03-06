import os
import re
import sys

from datetime import datetime, timedelta, tzinfo

try:
    import unittest2 as unittest
except ImportError:
    import unittest

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import ResponseFactory, XPathFunctions
from response_specs import ResponseBaseSpec, PlainObject, ComplexObject
from http_spec import WSGITestBase

ZERO = timedelta(0)

class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

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
            stylesheet='xpath_methods_spec.xsl'
            )

        #self.xpath = XPathCallbacks()

    def it_should_format_a_title(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/title.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Format Title</title></head><body>Format Title</body></html>')

    def it_should_format_to_lower(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/lower.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Lower-Case</title></head><body>lower-case</body></html>')

    def it_should_format_to_upper(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/upper.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Upper-Case</title></head><body>UPPER-CASE</body></html>')

    def it_should_strip_whitespace(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/whitespace.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Strip Whitespace</title></head><body>"whitespace"</body></html>')

    def it_should_coalesce_values(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/coalesce.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Coalesce</title></head><body>true</body></html>')

    def it_should_join_values_into_a_string(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/join.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Join</title></head><body><ul><li>this-is-a-test</li><li>1, 2</li></ul></body></html>')

    def it_should_replace_elements_in_a_string(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/replace.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Replace</title></head><body><p>this-is-a-test</p><p>-</p></body></html>')

    def it_should_reverse_elements(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/reverse.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Reverse Elements</title></head><body><ul><li>edcba</li><li><i>a</i><i>b</i><i>c</i><i>d</i><i>e</i></li><li><i>e</i><i>d</i><i>c</i><i>b</i><i>a</i></li></ul></body></html>')

    def it_should_format_a_date(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/date.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Format a Date</title></head><body><ul><li>Jan 01, 2010</li><li>Aug 21, 2000</li><li>Jan 09, 2010</li></ul></body></html>')

    def it_should_format_a_time(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/time.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Format a Time</title></head><body><ul><li>Jan 01, 2010</li><li>16:47:00 Jan 01, 2010</li><li>16:47:00</li><li>17:47:00 Jan 01, 2010</li><li>19:00:00 Dec 31, 2009</li><li>19:00:00 Dec 31, 2009</li><li>Friday January  1, 2010 at 12:00AM</li></ul></body></html>')

    def it_should_get_a_datetime_from_a_timestamp(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/timestamp.xsl'
            ).format()



        dt = datetime.utcnow()
        dt = dt.fromtimestamp(1346789137)
        dt = dt.replace(tzinfo=UTC())
        ts = []
        ts.append(dt.strftime('%Y-%m-%d %H:%M:%S%z'))
        ts.append(dt.strftime('%Y-%m-%d %H:%M:%S%z'))

        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Datetime From Timestamp</title></head><body><ul><li>%s</li><li>%s</li></ul></body></html>' % tuple(ts))

    def it_should_recognise_empty_values(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/empty.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Empty Tests</title></head><body><ul><li>true</li><li>true</li><li>true</li><li>true</li></ul></body></html>')

    def it_should_return_a_range(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/range.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Range</title></head><body><ul><li>0,1,2,3,4</li><li>0,2,4,6,8,10</li><li>10,9,8,7,6,5,4,3,2,1</li></ul></body></html>')

    def it_should_return_a_float_range(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/float_range.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Float Range</title></head><body>0.5,1.5,2.5,3.5,4.5</body></html>')

    def it_should_return_a_range_as_nodes(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/range_as_nodes.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Range of Nodes</title></head><body><range><i>0</i><i>1</i><i>2</i><i>3</i><i>4</i></range></body></html>')

    def it_should_return_a_float_range_as_nodes(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/float_range_as_nodes.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Float Range of Nodes</title></head><body><range><i>0.5</i><i>1.5</i><i>2.5</i><i>3.5</i><i>4.5</i></range></body></html>')

    def it_should_unescape_xml_entities(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/xml_entities.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>XML Entities</title></head><body><input value="&gt;&amp;&lt;"/></body></html>')

    def it_should_create_a_fragment(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/xml_fragment.xsl'
            ).format()
        self.assertEqual(response, '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Create a Fragment</title></head><body><ul><li><items><i>a</i><i>b</i><i>c</i><i>d</i><i>e</i></items></li></ul></body></html>')

    def it_should_call_a_method_successfully(self):
        response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='xpath/call_method.xsl'
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



class XPathResponseSpec(WSGITestBase):
    """XPath Spec (with complete request)"""

    def it_should_format_get_params(self):
        '''it should format GET params'''

        self.app.reset()
        self.app.config.formats['xsl'] = {
            'stylesheet': 'xpath/get_params.xsl',
            }
        self.app.router.clear()

        self.app.router.add('/', None)

        result = self.make_request('/', qs='foo=bar')

        self.assertEqual(result['body'], '<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Format GET Params</title></head><body><params><foo>bar</foo></params></body></html>')


    def it_should_get_parameters(self):
        self.skipTest('Not yet implemented')

    def it_should_get_session(self):
        self.skipTest('Not yet implemented')

    def it_should_get_environ(self):
        self.skipTest('Not yet implemented')

