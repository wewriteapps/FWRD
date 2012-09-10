from collections import MutableMapping as DictMixin
import datetime
import os
import re
import sys
import types

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from lxml import etree

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import ResponseFactory, ResponseTranslationError, \
     ResponseParameterError, XSLTranslationError

from util import assert_xpath

class PlainObject(object):
    pass

class ComplexObject(DictMixin):
    def __init__(self): self.dict = dict()
    def __delitem__(self, key): del self.dict[key]
    def __getitem__(self, key): return self.get(key, KeyError)
    def __iter__(self): return iter(self.dict)
    def __len__(self): return len(self.dict)
    def __setitem__(self, key, value): self.append(key, value)

    def get(self, key, default=None):
        if key not in self.dict:
            return default
        return self.dict[key]

class ResponseBaseSpec(unittest.TestCase):

    def _format_each_should_equal(self, items, contenttype=None):
        for test, expected in items:
            recieved = self.response.format(test)
            self.assertEqual(expected, recieved)

            if contenttype:
                self.assertEqual(self.response.headers['Content-Type'], contenttype)

    def _format_each_xpath(self, items, ns=None, contenttype=None):
        for test, expected, xpath in items:
            received = self.response.format(test)
            tree = etree.parse(StringIO(received))

            for x, v in xpath.iteritems():
                self._assert_xpath(tree, x, v, ns=ns)


# Monkey-patch the assert_xpath function on to the base class
#ResponseBaseSpec._assert_xpath = types.MethodType(assert_xpath, ResponseBaseSpec)
ResponseBaseSpec._assert_xpath = assert_xpath


class ResponseTypeSpec(unittest.TestCase):

    def it_should_create_a_plain_text_response_obj(self):
        self.assertEqual(
            ResponseFactory.new('txt', None, None).__class__.__name__,
            'TextResponse'
            )

        self.assertEqual(
            ResponseFactory.new('text', None, None).__class__.__name__,
            'TextResponse'
            )


    def it_should_create_an_xml_response_obj(self):
        self.assertEqual(
            ResponseFactory.new('xml', None, None).__class__.__name__,
            'XMLResponse'
            )


    def it_should_create_a_json_response_obj(self):
        self.assertEqual(
            ResponseFactory.new('json', None, None).__class__.__name__,
            'JSONResponse'
            )


    def it_should_create_a_translated_response_obj(self):
        self.assertEqual(
            ResponseFactory.new(None, None, None).__class__.__name__,
            'TranslatedResponse'
            )

        self.assertEqual(
            ResponseFactory.new('', None, None).__class__.__name__,
            'TranslatedResponse'
            )

        self.assertEqual(
            ResponseFactory.new('htm', None, None).__class__.__name__,
            'TranslatedResponse'
            )

        self.assertEqual(
            ResponseFactory.new('html', None, None).__class__.__name__,
            'TranslatedResponse'
            )


class TextResponseSpec(ResponseBaseSpec):

    def setUp(self):
        self.response = ResponseFactory.new('txt', None, None)

    def it_should_format_simple_responses(self):
        tests = (
            ('This is a response', 'This is a response'),
            )

        self._format_each_should_equal(tests, 'text/plain')

    def it_should_raise_when_formatting_a_python_obj(self):
        self.assertRaises(ResponseTranslationError,
                          self.response.format,
                          {'foo': 'bar'}
                          )

        class Foo(object):
            pass

        self.assertRaises(ResponseTranslationError,
                          self.response.format,
                          Foo()
                          )

class JsonResponseSpec(ResponseBaseSpec):
    """JSON response spec"""

    def setUp(self):
        self.response = ResponseFactory.new('json', None, None)

    def it_should_format_strings(self):
        tests = (
            ('This is a string', '"This is a string"'),
            )

        self._format_each_should_equal(tests, 'application/json')

    def it_should_format_boolean_True(self):
        tests = (
            (True, 'true'),
            )

        self._format_each_should_equal(tests, 'application/json')

    def it_should_format_boolean_False(self):
        tests = (
            (False, 'false'),
            )

        self._format_each_should_equal(tests, 'application/json')

    def it_should_format_standard_objects(self):
        class Foo(object):
            bar = True
            baz = False
            _hidden = "yes"
            def __init__(self):
                self.bar = False
                self.spam = (u'eggs', 'milk', {'bread': 2})
                self.today = datetime.date(2002, 3, 11)
                self.nothing = None

        tests = (
            (Foo(), '{"__name__":"Foo","bar":false,"nothing":null,"spam":["eggs","milk",{"bread":2}],"today":"2002-03-11"}'),
            )

        self._format_each_should_equal(tests, 'application/json')

    def it_should_format_lite_objects(self):
        class Foo(object):
            __slots__ = [
                'bar',
                'baz',
                'spam',
                'today',
                'nothing',
                '_hidden',
                ]
            def __init__(self):
                self.bar = True
                self.baz = False
                self._hidden = "yes"
                self.spam = (u'eggs', 'milk', {'bread': 2})
                self.today = datetime.date(2002, 3, 11)
                self.nothing = None

        tests = (
            (Foo(), '{"__name__":"Foo","bar":true,"baz":false,"nothing":null,"spam":["eggs","milk",{"bread":2}],"today":"2002-03-11"}'),
            )

        self._format_each_should_equal(tests, 'application/json')

    def it_should_format_an_empty_result(self):

        tests = (
            (None, '{}'),
            )

        self._format_each_should_equal(tests, 'application/json')


    def it_should_raise_when_unable_to_format_objects(self):
        self.skipTest('Not yet implemented')



class XmlResponseSpec(ResponseBaseSpec):
    """XML response spec"""

    def setUp(self):
        self.request = PlainObject()
        self.request.path = ('/', '/', '')
        self.request.route = '/'
        self.request.method = 'GET'
        self.response = ResponseFactory.new('xml', None, self.request)

    def it_should_format_simple_objects(self):
        tests = (
            (None, '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/" request="/" method="get"/>''', {
                 '/response/@route': '/',
                 '/response/@request': '/',
                 '/response/@method': 'get',
                 }),
            ('test', '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/" request="/" method="get">test</response>''', {
                 '/response/@route': '/',
                 '/response/@request': '/',
                 '/response/@method': 'get',
                 '/response': 'test',
                 }),
            )

        #self._format_each_should_equal(tests, 'application/xml')
        self._format_each_xpath(tests, contenttype='application/xml')

    def it_should_format_nested_unicode_dicts(self):
        tests = (
            ({u'foo': u'bar'},
             '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/" request="/" method="get">\n  <foo>bar</foo>\n</response>\n''', {
                 '/response/@route': '/',
                 '/response/@request': '/',
                 '/response/@method': 'get',
                 '/response/foo': 'bar',
                 }),
            ({u'foo': {u'bar': u'baz'}},
             '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/" request="/" method="get">
  <foo>
    <bar>baz</bar>
  </foo>
</response>''', {
                 '/response/@route': '/',
                 '/response/@request': '/',
                 '/response/@method': 'get',
                 '/response/foo/bar': 'baz',
                 }),
            ({u'details': [],
              u'terms': None,
              u'description': {
                  u'short': u'sldf',
                  u'long': u'skdjhfskjfdgn'
                  },
              u'title': u'meh',
              u'expires': datetime.datetime(2010, 2, 1, 0, 0),
              u'items': [],
              u'name': None,
              u'_id': '4d2596f7fa5bd80e18000001',
              u'type': None
              },
             """<?xml version='1.0' encoding='UTF-8'?>
<response route="/" request="/" method="get">
  <name/>
  <expires nodetype="timestamp">2010-02-01T00:00:00</expires>
  <terms/>
  <description>
    <short>sldf</short>
    <long>skdjhfskjfdgn</long>
  </description>
  <title>meh</title>
  <details nodetype="list"/>
  <type/>
  <items nodetype="list"/>
  <node name="_id">4d2596f7fa5bd80e18000001</node>
</response>
""", {
                 '/response/@route': '/',
                 '/response/@request': '/',
                 '/response/@method': 'get',
                 '/response/name': None,
                 '/response/terms': None,
                 '/response/type': None,
                 '/response/expires': '2010-02-01T00:00:00',
                 '/response/expires/@nodetype': 'timestamp',
                 '/response/description/short': 'sldf',
                 '/response/description/long': 'skdjhfskjfdgn',
                 '/response/title': 'meh',
                 '/response/node[@name="_id"]': '4d2596f7fa5bd80e18000001',
                 '/response/details/@nodetype': 'list',
                 '/response/details': None,
                 '/response/items/@nodetype': 'list',
                 '/response/items': None,
                 }),
            )

        #self._format_each_should_equal(tests, 'application/xml')
        self._format_each_xpath(tests, contenttype='application/xml')


    def it_should_format_special_characters(self):
        tests = (
            ('< & >', '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/" request="/" method="get">&lt; &amp; &gt;</response>''', {
                 '/response/@route': '/',
                 '/response/@request': '/',
                 '/response/@method': 'get',
                 '/response': '< & >',
                 }),
            )

        #self._format_each_should_equal(tests, 'application/xml')
        self._format_each_xpath(tests, contenttype='application/xml')


    def it_should_format_newlines(self):
        tests = (
            ('''This

is

a

long

paragraph

''', '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<response route="/" request="/" method="get">This

is

a

long

paragraph

</response>''', {
                 '/response/@route': '/',
                 '/response/@request': '/',
                 '/response/@method': 'get',
                 '/response': '''This

is

a

long

paragraph

''',
                 }),
            (('''This

is

a''', '''

long

paragraph

'''), '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<response route="/" request="/" method="get" nodetype="fixed-list">
  <i>This

is

a</i>
  <i>

long

paragraph

</i>
</response>
''', {
                 '/response/@route': '/',
                 '/response/@request': '/',
                 '/response/@method': 'get',
                 '/response/i[1]': '''This

is

a''',
                 '/response/i[2]': '''

long

paragraph

''',
                 }),
            )

        #self._format_each_should_equal(tests, 'application/xml')
        self._format_each_xpath(tests, contenttype='application/xml')


    def it_should_format_complex_objects(self):

        nesteddict = {
            'foo': set([1,2,3]),
            'bar': False,
            'baz': {
                'a': (1,2,3),
                'b': datetime.date(2002, 3, 11),
                'c': "{36980915-cd66-4547-9081-760ad0d77625}"
                }
            }

        foo = PlainObject()
        foo.bar = 'baz'
        foo.nested = nesteddict

        tests = (
            ((1,2,3), '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/" request="/" method="get" nodetype="fixed-list">
  <i>1</i>
  <i>2</i>
  <i>3</i>
</response>
''', {
                 '/response/@route': '/',
                 '/response/@request': '/',
                 '/response/@method': 'get',
                 '/response/@nodetype': 'fixed-list',
                 '/response/i[1]': '1',
                 '/response/i[2]': '2',
                 '/response/i[3]': '3',
                 }),
            (['foo','bar',True],
             '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/" request="/" method="get" nodetype="list">
  <i>foo</i>
  <i>bar</i>
  <i nodetype="boolean">true</i>
</response>
''', {
                 '/response/@route': '/',
                 '/response/@request': '/',
                 '/response/@method': 'get',
                 '/response/@nodetype': 'list',
                 '/response/i[1]': 'foo',
                 '/response/i[2]': 'bar',
                 '/response/i[3]': 'true',
                 '/response/i[3]/@nodetype': 'boolean',
                 }),
            ((i for i in [1,2,3]),
             '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/" request="/" method="get" nodetype="generated-list">
  <i>1</i>
  <i>2</i>
  <i>3</i>
</response>
''', {
                 '/response/@route': '/',
                 '/response/@request': '/',
                 '/response/@method': 'get',
                 '/response/@nodetype': 'generated-list',
                 '/response/i[1]': '1',
                 '/response/i[2]': '2',
                 '/response/i[3]': '3',
                 }),
            (nesteddict,
             '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/" request="/" method="get">
  <baz>
    <a nodetype="fixed-list">
      <i>1</i>
      <i>2</i>
      <i>3</i>
    </a>
    <c nodetype="uuid">{36980915-cd66-4547-9081-760ad0d77625}</c>
    <b nodetype="timestamp">2002-03-11</b>
  </baz>
  <foo nodetype="unique-list">
    <i>1</i>
    <i>2</i>
    <i>3</i>
  </foo>
  <bar nodetype="boolean">false</bar>
</response>
''', {
                 '/response/@route': '/',
                 '/response/@request': '/',
                 '/response/@method': 'get',
                 '/response/baz/a/i[1]': '1',
                 '/response/baz/c/@nodetype': 'uuid',
                 '/response/baz/c': '{36980915-cd66-4547-9081-760ad0d77625}',
                 '/response/foo/@nodetype': 'unique-list',
                 '/response/foo/i[1]': '1',
                 }),
            (foo,
             '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/" request="/" method="get">
  <PlainObject nodetype="container">
    <bar>baz</bar>
    <nested>
      <baz>
        <a nodetype="fixed-list">
          <i>1</i>
          <i>2</i>
          <i>3</i>
        </a>
        <c nodetype="uuid">{36980915-cd66-4547-9081-760ad0d77625}</c>
        <b nodetype="timestamp">2002-03-11</b>
      </baz>
      <foo nodetype="unique-list">
        <i>1</i>
        <i>2</i>
        <i>3</i>
      </foo>
      <bar nodetype="boolean">false</bar>
    </nested>
  </PlainObject>
</response>
''', {
                 '/response/@route': '/',
                 '/response/@request': '/',
                 '/response/@method': 'get',
                 '/response/PlainObject/@nodetype': 'container',
                 '/response/PlainObject/bar': 'baz',
                 '/response/PlainObject/nested/baz/c': '{36980915-cd66-4547-9081-760ad0d77625}',
                 '/response/PlainObject/nested/baz/b': '2002-03-11',
                 }),
            )

        #self._format_each_should_equal(tests, 'application/xml')
        self._format_each_xpath(tests, contenttype='application/xml')


    def it_should_raise_when_unable_to_format_objects(self):
        self.skipTest('Not yet implemented')



class TranslatedResponseSpec(ResponseBaseSpec):
    """Translated (XSL) response spec"""

    def setUp(self):
        self.request = PlainObject()
        self.request.path = ('/', '/', '')
        self.request.route = '/'
        self.request.method = 'GET'
        self.response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='translated_response_spec.xsl'
            )

    def it_should_raise_when_stylesheet_cannot_be_found(self):
        self.response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='non-existant-stylesheet.xsl'
            )

        self.assertRaises(ResponseParameterError,
                          self.response.format)

    def it_should_raise_when_stylesheet_directory_cannot_be_found(self):
        self.response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='non-existant-path/default.xsl'
            )

        self.assertRaises(ResponseParameterError,
                          self.response.format)


    def it_should_raise_when_unable_to_format_objects(self):
        self.skipTest('Not yet implemented')


    def it_should_raise_when_stylesheet_is_broken(self):
        self.response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='broken-stylesheet.xsl'
            )

        self.assertRaises(XSLTranslationError,
                          self.response.format)


    def it_should_raise_for_stylesheet_errors(self):
        self.response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='failing-stylesheet.xsl'
            )

        self.assertRaises(XSLTranslationError,
                          self.response.format)


    def it_should_format_simple_objects(self):
        tests = (
            (None, '''<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Basic HTML Response</title></head><body/></html>'''),
            ('test', '''<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Basic HTML Response</title></head><body>test</body></html>'''),
            )

        self._format_each_should_equal(tests, 'text/html')


    def it_should_format_complex_objects(self):
        tests = (
            ({"tuple": (1,2,3)}, '''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>Basic HTML Response</title></head><body>
  <ol><li>1</li><li>2</li><li>3</li></ol>
</body></html>'''),
            )

        self._format_each_should_equal(tests, 'text/html')



class TranslatedWithVarsResponseSpec(ResponseBaseSpec):
    """Translated (XSL, with vars) response spec"""

    def setUp(self):
        self.request = ComplexObject()
        self.request.path = ('/', '/', '')
        self.request.route = '/'
        self.request.method = 'GET'
        self.request.session = {}
        self.request.params = {}
        self.response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='translation_with_vars_spec.xsl'
            )

    def it_should_format_simple_objects(self):
        tests = (
            (None, '''<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Basic HTML Response</title></head><body/></html>'''),
            ('test', '''<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Basic HTML Response</title></head><body>test</body></html>'''),
            )

        self._format_each_should_equal(tests, 'text/html')


    def it_should_format_complex_objects(self):
        tests = (
            ({"tuple": (1,2,3)}, '''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>Basic HTML Response</title></head><body>
  <ol><li>1</li><li>2</li><li>3</li></ol>
</body></html>'''),
            )

        self._format_each_should_equal(tests, 'text/html')

class TranslatedWithImportsResponseSpec(ResponseBaseSpec):
    """Translated (XSL with imported stylesheets) response spec"""

    def setUp(self):
        self.request = ComplexObject()
        self.request.path = ('/', '/', '')
        self.request.route = '/'
        self.request.method = 'GET'
        self.request.session = {}
        self.request.params = {}
        self.response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet='translation_with_imports_spec.xsl'
            )

    def it_should_format_simple_objects(self):
        tests = (
            (None, '''<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Basic HTML Response</title></head><body/></html>'''),
            ('test', '''<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8"/><title>Basic HTML Response</title></head><body>test</body></html>'''),
            )

        self._format_each_should_equal(tests, 'text/html')


    def it_should_format_complex_objects(self):
        tests = (
            ({"tuple": (1,2,3)}, '''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>Basic HTML Response</title></head><body>
  <ol><li>1</li><li>2</li><li>3</li></ol>
</body></html>'''),
            )

        self._format_each_should_equal(tests, 'text/html')


class DirectResponseSpec(ResponseBaseSpec):
    def setUp(self):
        self.response = ResponseFactory.new('direct', None, None)

    def it_should_format_simple_responses(self):
        tests = (
            ('This is a response', 'This is a response'),
            )

        self._format_each_should_equal(tests)
