import os
import re
import sys
import unittest

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import ParameterContainer



class ParameterContainerSpec(unittest.TestCase):
    def setUp(self):
        pass

    def it_should_parse_simple_params_correctly(self):
        tests = {
            'a=1&b=2&c=3': {'a': 1,
                            'b': 2,
                            'c': 3,
                            }
            }

        self._test_items(tests)

    def it_should_parse_repeated_params_correctly(self):
        tests = {
            'a=1&a=2&a=3': {'a': [1,2,3]}
            }

        self._test_items(tests)

    def it_should_parse_boolean_params_correctly(self):
        tests = {
            'a=true': {'a': True},
            'b=false': {'b': False},
            }

        self._test_items(tests)

    def it_should_parse_empty_params_correctly(self):
        tests = {
            'a=': {'a': None},
            'b=none': {'b': 'none'},
            }

        self._test_items(tests)

    def it_should_parse_float_params_correctly(self):
        tests = {
            'a=1.0': {'a': float('1.0')},
            'b=-2.4': {'b': float('-2.4')},
            'c=53.1,32.2': {'c': "53.1,32.2"},
            }

        self._test_items(tests)

    def it_should_parse_named_params_correctly(self):
        tests = {
            'a[foo]=1': {'a': {'foo': 1}},
            'a[foo][bar]=1': {'a': {'foo': {'bar': 1}}},
            'a[foo]=1&a[bar]=2': {'a': {'foo': 1, 'bar': 2}}
            }

        self._test_items(tests)

    def it_should_parse_sequenced_params_correctly(self):
        tests = {
            #'a[]=1': {'a': {'_': 1}},
            #'a[]=1&a[]=2': {'a': {'_': [1,2]}},
            'a[]=1&a=2&a=3': {'a': [1,2,3]},
            #'a=1&a=2&a=3': {'a': {'_': [1,2,3]}},
            }

        self._test_items(tests)

    def it_should_parse_mixed_params_correctly(self):
        tests = {
            'a[]=1&a[]=2&a[foo]=3': {'a': {'foo': 3}},
            'a=1&b[]=2&b[]=3&baz=true&b=4&b[foo]=bar&tel=01234567890': {
                'a': 1,
                'baz': True,
                'tel': '01234567890',
                'b': {'foo': 'bar'},
                },
            'a[x]=1&a[y]=2&a[z][]=3&a[z][]=4&a[z][]=5&b[foo][0]=foo&b[foo][1]=bar': {
                'a': {
                    'x': 1,
                    'y': 2,
                    'z': [3,4,5],
                    },
                'b': {'foo': {
                    '0': 'foo',
                    '1': 'bar',
                    }},
                },
            'a[x]=1&a[y]=2&a[z][]=3&a[z][]=4&a[z][]=5&b[][0]=foo&b[][1]=bar': {
                'a': {
                    'x': 1,
                    'y': 2,
                    'z': [3,4,5],
                    },
                'b': {'_': {
                    '0': 'foo',
                    '1': 'bar',
                    }},
                },
            'a[x]=1&a[y]=2&a[z][]=3&a[z][]=4&a[z][]=5&b[][]=foo&b[][]=bar': {
                'a': {
                    'x': 1,
                    'y': 2,
                    'z': [3,4,5],
                    },
                'b': {'_': ['foo', 'bar']}
                }
            }

        self._test_items(tests)

    def it_should_overwrite_params_correctly(self):
        tests = {
            'a[]=1&a=2&a[spam]=eggs': {'a': {'spam': 'eggs'}},
            'a[spam]=eggs&a=1&a[]=2': {'a': [1,2]},
            }

        self._test_items(tests)

    def _test_items(self, items):
        for key, value in items.iteritems():
            blob = ParameterContainer().parse_qs(key)
            self.assertEqual(blob, value)
