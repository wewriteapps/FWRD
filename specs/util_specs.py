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

from FWRD import CaseInsensitiveDict, CaseInsensitiveDictMapper


class CaseInsensitiveDictSpec(unittest.TestCase):
    '''Utility Class/Method Specs: Case-insensitive dicts'''

    def setUp(self):
        pass

    def ensure_ci_dict_acts_as_dict(self):
        d = CaseInsensitiveDict({
            'aAa': 1,
            'Bbb': True,
            'CCC': False
            })

        self.assertEqual(d['AaA'], 1)
        self.assertTrue(d['BBB'])
        self.assertFalse(d['ccc'])

class CaseInsensitiveDictMapperSpec(unittest.TestCase):
    '''Utility Class/Method Specs: Case-insensitive dict mapping method'''

    def ensure_nested_dicts_are_mapped_correctly(self):
        d = {
            'AaA': 1,
            'BbB': ['a', 'B', {'CCc': True}],
            'Ccc': {
                'FOO': 1,
                'BaR': set(['a', 'B', 'CCc'])
                }
            }

        d = CaseInsensitiveDictMapper(d)

        self.assertEqual(d['aaa'], 1)
        self.assertEqual(d['bbb'][2]['ccc'], True)
        self.assertEqual(d['ccc']['foo'], 1)
        self.assertEqual(type(d['ccc']['bar']), set)
        self.assertEqual(list(d['ccc']['bar'])[-1], 'CCc')

