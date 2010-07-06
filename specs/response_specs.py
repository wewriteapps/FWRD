import datetime
import os
import re
import sys
import unittest

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import ResponseFactory, ResponseTranslationError, ResponseParameterError

class PlainObject(object):
    pass

class ResponseBaseSpec(unittest.TestCase):

    def _format_each_should_equal(self, items, contenttype=None):
        for test, expected in items:
            recieved = self.response.format(test)
            self.assertEqual(expected, recieved)

            if contenttype:
                self.assertEqual(self.response.headers['Content-Type'], contenttype)


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

    def it_should_format_complex_objects(self):
        class Foo(object):
            bar = True
            baz = False
            def __init__(self):
                self.spam = (u'eggs', 'milk', {'bread': 2})
                self.today = datetime.date(2002, 3, 11)
                
        tests = (
            (Foo(), '{"__name__":"Foo","bar":true,"baz":false,"spam":["eggs","milk",{"bread":2}],"today":"2002-03-11"}'),
            )

        self._format_each_should_equal(tests, 'application/json')

    """
    def it_should_raise_when_unable_to_format_objects(self):
        self.fail('Not Implemented')
    """

    
class XmlResponseSpec(ResponseBaseSpec):

    def setUp(self):
        self.request = PlainObject()
        self.request.path = ('/', '/', '')
        self.request.route = '/'
        self.request.method = 'GET'
        self.response = ResponseFactory.new('xml', None, self.request)

    def it_should_format_simple_objects(self):
        tests = (
            (None, '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<response route="/" request="/" method="get"/>'),
            ('test', '<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<response route="/" request="/" method="get">test</response>'),
            )

        self._format_each_should_equal(tests, 'application/xml')

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
'''),
            (['foo','bar',True],
             '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/" request="/" method="get" nodetype="list">
  <i>foo</i>
  <i>bar</i>
  <i nodetype="boolean">true</i>
</response>
'''),
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
'''),
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
'''),
            )

        self._format_each_should_equal(tests, 'application/xml')

    """
    def it_should_raise_when_unable_to_format_objects(self):
        self.fail('Not Implemented')
    """


class TranslatedResponseSpec(ResponseBaseSpec):

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
            default_stylesheet='translated_response_spec.xsl'
            )

    def it_should_raise_when_stylesheet_cannot_be_found(self):
        self.response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='.',
            default_stylesheet='non-existant-stylesheet.xsl'
            )

        self.assertRaises(ResponseParameterError,
                          self.response.format)

    def it_should_raise_when_stylesheet_directory_cannot_be_found(self):
        self.response = ResponseFactory.new(
            None,
            None,
            self.request,
            stylesheet_path='non-existant-path',
            default_stylesheet='default.xsl'
            )

        self.assertRaises(ResponseParameterError,
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
        
    """
    def it_should_raise_when_unable_to_format_objects(self):
        self.fail('Not Implemented')
    """

