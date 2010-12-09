import os
import re
import sys
import unittest

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from http_spec import WSGITestBase

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import Request, ResponseParameterError


class GetRequestSpec(WSGITestBase):
    """GET request spec"""

    def setUp(self):
        super(self.__class__, self).setUp()
        self.app.reset()
        self.app.config.format['xsl'] = {
            'stylesheet_path': 'specs',
            'default_stylesheet': 'translated_response_spec.xsl',
            }
        self.app.router.clear()

    def it_should_parse_file_extensions_correctly(self):
        self.app.router.add('/foo/bar', None)
        self.make_request('/foo/bar.baz')
        self.assertEqual('baz', self.app.request.path[1])

        self.app.router.add('/foo.bar/boz', None)
        self.make_request('/foo.bar/boz.baz')
        self.assertEqual('baz', self.app.request.path[1])

    def it_should_parse_GET_params_correctly(self):
        self.app.router.add('/', None)
        self.make_request('/', qs='a=1&b[]=2&b[]=3&baz=true&b=4&b[foo]=bar&tel=01234567890')

        params = {
            'a': 1,
            'b': {'foo': 'bar'},
            'baz': True,
            'tel': '01234567890'
            }

        for key, value in params.iteritems():
            self.assert_(key in self.app.request['GET'])
            self.assertEqual(value, self.app.request['GET'][key])

    def it_should_parse_float_params_correctly(self):
        self.app.router.add('/', None)
        self.make_request('/', qs='a=1.0&b=-2.4&c=53.1,32.2')

        params = {
            'a': float('1.0'),
            'b': float('-2.4'),
            'c': "53.1,32.2"
            }

        for key, value in params.iteritems():
            self.assert_(key in self.app.request['GET'])
            self.assertEqual(value, self.app.request['GET'][key])

    def it_should_match_basic_routes_correctly(self):
        routes = ['/', '/foo', '/bar']
        for route in routes:
            self.app.router.add(route, None)

        for route in routes:
            self.assertStatus(200, route=route)

    def it_should_match_parametered_routes_correctly(self):

        def foo(foo):
            pass

        def bar(dept, name=None):
            pass
        
        routes = {
            ('/:foo', foo): {
                '/meh': {
                    'foo': 'meh'
                    },
                '/blah': {
                    'foo': 'blah'
                    }
                },
            ('/company/:dept[/:name]', bar): {
                '/company/it': {
                    'dept': 'it'
                    },
                '/company/it/support': {
                    'dept': 'it',
                    'name': 'support'
                    },
                '/company/hr/grievance%20councelling': {
                    'dept': 'hr',
                    'name': 'grievance councelling'
                    }
                }
            }

        for route, requests in routes.iteritems():
            self.app.router.add(route[0], route[1])

            for request, params in requests.iteritems():
                self.make_request(request)

                for name, value in params.iteritems():
                    self.assert_(name in self.app.request.PATH)
                    self.assert_(name in self.app.request.params)
                    self.assertEqual(value, self.app.request.PATH[name])
                    self.assertEqual(value, self.app.request.params[name])

    def it_should_format_responses_correctly(self):

        def index():
            return "index"

        def foo():
            return {
                'a': True,
                'b': False
                }

        routes = (
            # route, extension, func, body
            ('/', '.xml', index, '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/" request="/" method="get">
  <content>index</content>
  <errors/>
</response>
'''),
            ('/foo', '.xml', foo, '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/foo" request="/foo" method="get">
  <content>
    <a nodetype="boolean">true</a>
    <b nodetype="boolean">false</b>
  </content>
  <errors/>
</response>
'''),
            )

        for route, ext, func, body in routes:
            self.app.router.add(route, func)

        for route, ext, func, body in routes:
            self.assertBody(body, route+ext)

    def it_should_format_whitespace_correctly(self):

        def bar():
            return """This is a long string

With lots of whitespace

    To show correct formatting

"""

        routes = (
            # route, extension, func, body
            ('/bar', '.xml', bar, '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/bar" request="/bar" method="get">
  <content>This is a long string

With lots of whitespace

    To show correct formatting

</content>
  <errors/>
</response>
'''),
            )

        for route, ext, func, body in routes:
            self.app.router.add(route, func)

        for route, ext, func, body in routes:
            self.assertBody(body, route+ext)
        

    def it_should_ignore_additional_qs_args(self):

        def foo(foo): pass
        self.app.router.add('/unexpected_params', foo)
        self.assertStatus(200, '/unexpected_params.xml', qs='foo=1&bar=2')
        self.assertBody('''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/unexpected_params" request="/unexpected_params" method="get">
  <content/>
  <errors/>
</response>
''', '/unexpected_params.xml', qs='foo=1&bar=2')



    def it_should_process_filters_successfully(self):
        config = StringIO('''
Routes:
  - route: /[index]
    filters:
      - callable: specs.example_methods:basic_filter
        args:
          message: hello world
        ''')

        self.assertTrue(self.app.setup(config) != False)
        self.assertStatus(200, '/index.xml')
        self.assertBody('''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/[index]" request="/index" method="get">
  <content nodetype="fixed-list">
    <i>hello world</i>
    <i/>
  </content>
  <errors/>
</response>
''', '/index.xml')


    def it_should_process_multiple_filters_successfully(self):
        config = StringIO('''
Routes:
  - route: /[index]
    filters:
      - callable: specs.example_methods:hello_filter
      - callable: specs.example_methods:world_filter
        ''')

        self.assertTrue(self.app.setup(config) != False)
        self.assertStatus(200, '/index.xml')
        self.assertBody('''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/[index]" request="/index" method="get">
  <content nodetype="fixed-list">
    <i>hello</i>
    <i nodetype="fixed-list">
      <i>world</i>
      <i/>
    </i>
  </content>
  <errors/>
</response>
''', '/index.xml')


    def it_should_process_global_filters_correctly(self):
        config = StringIO('''
Global Filters:
  - callable: specs.example_methods:hello_filter
Routes:
  - route: /[index]
    filters:
      - callable: specs.example_methods:world_filter
        ''')

        self.assertTrue(self.app.setup(config) != False)
        self.assertStatus(200, '/index.xml')
        self.assertBody('''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/[index]" request="/index" method="get">
  <content nodetype="fixed-list">
    <i>hello</i>
    <i nodetype="fixed-list">
      <i>world</i>
      <i/>
    </i>
  </content>
  <errors/>
</response>
''', '/index.xml')




class PostRequestSpec(WSGITestBase):
    '''POST request spec'''

    def setUp(self):
        super(self.__class__, self).setUp()
        self.app.config.format['xsl'] = {
            'stylesheet_path': 'specs',
            'default_stylesheet': 'translated_response_spec.xsl',
            }


    def it_should_parse_params_correctly(self):
        self.app.router.add('/', None, methods='GET,POST')
        self.make_request('/', method='POST', qs='a=1&b[]=2&b[]=3&baz=true&b=4&b[foo]=bar&tel=01234567890')

        params = {
            'a': 1,
            'b': {'foo': 'bar'},
            'baz': True,
            'tel': '01234567890'
            }

        self.assertEqual(self.app.request['POST'], params)
        
        '''
        for key, value in params.iteritems():
            self.assert_(key in self.app.request['POST'])
            self.assertEqual(value, self.app.request['POST'][key])
        '''

    def it_should_parse_grouped_params_correctly(self):
        self.app.router.add('/', None, methods='POST')
        self.make_request('/', method='POST', qs="a[x]=1&a[y]=2&a[z][]=3&a[z][]=4&a[z][]=5&b[foo][0]=foo&b[foo][1]=bar")

        params = {
            'a': {
                'x': 1,
                'y': 2,
                'z': [3,4,5],
                },
            'b': {'foo': {
                '0': 'foo',
                '1': 'bar',
                }},
            }

        self.assertEqual(self.app.request['POST'], params)

        '''
        for key, value in params.iteritems():
            print key, value, self.app.request['POST']
            self.assert_(key in self.app.request['POST'])
            self.assertEqual(value, self.app.request['POST'][key])
        '''


    """
    def it_should_parse_multipart_posts_correctly(self):
        self.fail('Not yet implemented)

    def ensure_get_does_not_clobber_post_params(self):
        self.fail('Not yet implemented)

    def it_should_not_allow_incorrect_content_length(self):
        self.fail('Not yet implemented)

    """

