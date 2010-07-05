import datetime
import os
import re
import sys
import unittest

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import ResponseFactory, ResponseTranslationError

class ResponseTypeSpec(unittest.TestCase):

    def it_should_create_a_plain_text_response_obj(self):
        self.assertEqual(
            ResponseFactory.new('txt', object).__class__.__name__,
            'TextResponse'
            )        

        self.assertEqual(
            ResponseFactory.new('text', object).__class__.__name__,
            'TextResponse'
            )        


    def it_should_create_an_xml_response_obj(self):
        self.assertEqual(
            ResponseFactory.new('xml', object).__class__.__name__,
            'XMLResponse'
            )        

 
    def it_should_create_a_json_response_obj(self):
        self.assertEqual(
            ResponseFactory.new('json', object).__class__.__name__,
            'JSONResponse'
            )        


    def it_should_create_a_translated_response_obj(self):
        self.assertEqual(
            ResponseFactory.new(None, object).__class__.__name__,
            'TranslatedResponse'
            )        

        self.assertEqual(
            ResponseFactory.new('', object).__class__.__name__,
            'TranslatedResponse'
            )        

        self.assertEqual(
            ResponseFactory.new('htm', object).__class__.__name__,
            'TranslatedResponse'
            )        

        self.assertEqual(
            ResponseFactory.new('html', object).__class__.__name__,
            'TranslatedResponse'
            )

    def _format_each_should_equal(self, items):
        for test, expected in items:
            recieved = self.response.format(test)
            self.assertEqual(expected, recieved)


class TextResponseSpec(unittest.TestCase):

    def setUp(self):
        self.response = ResponseFactory.new('txt', None)

    def it_should_format_simple_responses(self):
        parameter = 'This is a response'
        expected = 'This is a response'
        recieved = self.response.format(parameter)

        self.assertEqual(expected, recieved)

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

class JsonResponseSpec(ResponseTypeSpec):

    def setUp(self):
        self.response = ResponseFactory.new('json', None)

    def it_should_format_strings(self):
        tests = (
            ('This is a string', '"This is a string"'),
            )

        self._format_each_should_equal(tests)

    def it_should_format_boolean_True(self):
        tests = (
            (True, 'true'),
            )

        self._format_each_should_equal(tests)

    def it_should_format_boolean_False(self):
        tests = (
            (False, 'false'),
            )

        self._format_each_should_equal(tests)

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

        self._format_each_should_equal(tests)

    def it_should_raise_when_unable_to_format_objects(self):
        pass

    
class XmlResponseSpec(unittest.TestCase):

    def setUp(self):
        self.response = ResponseFactory.new('xml', None)

    def it_should_format_simple_objects(self):
        pass

    def it_should_format_complex_objects(self):
        pass

    def it_should_raise_when_unable_to_format_objects(self):
        pass


class TranslatedResponseSpec(unittest.TestCase):

    def setUp(self):
        self.response = ResponseFactory.new(None, None)

    def it_should_format_simple_objects(self):
        pass

    def it_should_format_complex_objects(self):
        pass

    def it_should_raise_when_unable_to_format_objects(self):
        pass


