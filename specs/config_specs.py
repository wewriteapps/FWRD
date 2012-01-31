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

from FWRD import application, router, Route, ConfigError, RouteCompilationError


class ConfigSpec(unittest.TestCase):
    '''Configuration Import spec'''

    def setUp(self):
        router.clear()

    def it_should_import_successfully(self):
        configs = ('''
Config:
  app_path: %s
  port: 8200
''', '''
Config:
  app_path: %s
Routes:
  - route: /[index]
''',)

        for config in configs:
            config = StringIO(config % os.path.dirname(os.path.abspath(__file__)))
            self.assertTrue(application.setup(config))


    def it_should_import_from_a_file(self):
        self.assertTrue(application.setup('setup_test.yaml'))


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
Config:
  app_path: %s
Routes:
  - route: /[index]
  - route: /foo
    callable: specs.example_methods:foo
    methods: [GET, POST]
  - route: /bar/:id
    callable: specs.example_methods:Bar().bar
    ''',)

        for config in configs:
            config = StringIO(config % os.path.dirname(os.path.abspath(__file__)))
            application.setup(config)
            self.assertEqual(len(router.urls['GET']), 3)
            self.assertEqual(len(router.urls['POST']), 1)


    def it_should_parse_parametered_routes_with_no_callable(self):
        config = '''
Config:
  app_path: %s
Routes:
  - route: /:foo
        '''
        application.setup(StringIO(config % os.path.dirname(os.path.abspath(__file__))))
        self.assertEqual(len(router.urls['GET']), 1)


    def it_should_parse_a_parametered_index_route_with_callable(self):
        config = '''
Config:
  app_path: %s
Routes:
  - route: /:eggs
    callable: specs.example_methods:spam
        '''
        application.setup(StringIO(config % os.path.dirname(os.path.abspath(__file__))))
        self.assertEqual(len(router.urls['GET']), 1)


    def it_should_not_parse_a_route_without_a_callable(self):
        config = StringIO('''
Config:
  app_path: %s
Routes:
  - callable: specs.example_methods:foo
        ''' % os.path.dirname(os.path.abspath(__file__)))
        self.assertRaises(RouteCompilationError,
                          application.setup,
                          config)


    def it_should_add_filters_successfully(self):
        configs = ('''
Config:
  app_path: %s
Routes:
  - route: /[index]
    filters:
      - callable: specs.example_methods:basic_filter
        args:
          message: hello world
        ''',)

        for config in configs:
            config = StringIO(config % os.path.dirname(os.path.abspath(__file__)))
            application.setup(config)
            route = router.urls['GET'].values()[0]
            filter_ = [dict(x) for x in route.request_filters][0]
            self.assertEqual(filter_['callable'], 'specs.example_methods:basic_filter')
            self.assertTrue('args' in filter_)


    def it_should_fail_on_incorrect_filters(self):
        config = StringIO('''
Config:
  app_path: %s
Routes:
  - route: /[index]
    filters: specs.example_methods:basic_filter
''' % os.path.dirname(os.path.abspath(__file__)))
        self.assertRaises(RouteCompilationError,
                          application.setup,
                          config)
                          

    def it_should_add_global_filters(self):

        config = '''
Config:
  app_path: %s
Global Filters:
  - callable: specs.example_methods:basic_filter
Routes:
  - route: /[index]
'''

        application.setup(StringIO(config % os.path.dirname(os.path.abspath(__file__))))
        self.assertEqual(
            application.router._global_filters,
            [{'callable': 'specs.example_methods:basic_filter'}]
            )

    def it_should_configure_formatters(self):

        config = '''
Config:
  port: 8080
  app_path: %s
  formats:
    default: xsl
    xsl:
      enabled: true
      stylesheet: xsl/default.xsl
    json:
      enabled: true
    yaml:
      enabled: false
Routes:
  - route: /[index]
'''

        application.setup(StringIO(config % os.path.dirname(os.path.abspath(__file__))))
        '''
        self.assertEqual(
            application.
            )
        '''
