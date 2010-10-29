import os
import re
import sys
import unittest

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import application, router, ConfigError


class ConfigSpec(unittest.TestCase):
    '''Configuration Import spec'''

    def setUp(self):
        pass


    def it_should_import_successfully(self):
        configs = ('''
Config:
  port: 8200
''', '''
Routes:
  - route: /[index]
''',
                   )

        for config in configs:
            config = StringIO(config)
            self.assertTrue(application.import_config(config) != False)
            

    def it_must_raise_for_malformed_config(self):
        configs = (
            "unbalanced brackets: ][",
            )

        for config in configs:
            config = StringIO(config)
            self.assertRaises(ConfigError,
                              application.import_config,
                              config)


    def it_must_raise_for_invalid_config(self):
        configs = (
            "foo: Yes",
            )

        for config in configs:
            config = StringIO(config)
            self.assertRaises(ConfigError,
                              application.import_config,
                              config)

    def it_should_add_routes_successfully(self):

        def foo(): pass
        
        configs = ('''
Routes:
  - route: /[index]
  - route: /foo
    callable: foo
    methods: [GET, POST]''',)

        for config in configs:
            config = StringIO(config)
            application.import_config(config)
            self.assertEqual(len(router.urls['GET']), 2)
            self.assertEqual(len(router.urls['POST']), 1)
