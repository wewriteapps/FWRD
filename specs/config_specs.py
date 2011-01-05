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

from FWRD import application, router, Route, ConfigError


class ConfigSpec(unittest.TestCase):
    '''Configuration Import spec'''

    def setUp(self):
        router.clear()

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
            self.assertTrue(application.setup(config) != False)


    def it_should_import_from_a_file(self):
        self.assertTrue(application.setup('specs/setup_test.yaml') != False)
            

    def it_must_raise_for_malformed_config(self):
        configs = (
            "unbalanced brackets: ][",
            )

        for config in configs:
            config = StringIO(config)
            self.assertRaises(ConfigError,
                              application.setup,
                              config)


    def it_must_raise_for_invalid_config(self):
        configs = (
            "foo: Yes",
            )

        for config in configs:
            config = StringIO(config)
            self.assertRaises(ConfigError,
                              application.setup,
                              config)

    def it_should_add_routes_successfully(self):

        configs = ('''
Routes:
  - route: /[index]
  - route: /foo
    callable: specs.example_methods:foo
    methods: [GET, POST]
  - route: /bar/:id
    callable: specs.example_methods:Bar().bar
    ''',)

        for config in configs:
            config = StringIO(config)
            application.setup(config)
            self.assertEqual(len(router.urls['GET']), 3)
            self.assertEqual(len(router.urls['POST']), 1)


    def it_should_add_filters_successfully(self):
        configs = ('''
Routes:
  - route: /[index]
    filters:
      - callable: specs.example_methods:basic_filter
        args:
          message: hello world
        ''',)

        for config in configs:
            config = StringIO(config)
            application.setup(config)
            route = router.urls['GET'].values()[0]
            filter_ = [dict(x) for x in route.request_filters][0]
            self.assertEqual(filter_['callable'], 'specs.example_methods:basic_filter')
            self.assertTrue('args' in filter_)

    def it_should_add_global_filters(self):

        config = '''
Global Filters:
  - callable: specs.example_methods:basic_filter
Routes:
  - route: /[index]
'''

        print 'setting config'
        application.setup(StringIO(config))
        print 'running tests'
        self.assertEqual(application.router._global_filters, [{'callable': 'specs.example_methods:basic_filter'}])
            
