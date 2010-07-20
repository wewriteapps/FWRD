import os
import re
import sys
import unittest

from http_spec import WSGITestBase

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import Request, ResponseParameterError


class GetRequestSpec(WSGITestBase):
    """GET request spec"""

    def setUp(self):
        super(self.__class__, self).setUp()
        self.app.config.format['xsl'] = {
            'stylesheet_path': 'specs',
            'default_stylesheet': 'translated_response_spec.xsl',
            }

    def it_should_parse_file_extensions_correctly(self):
        self.app.router.add('/foo/bar', None)
        self.make_request('/foo/bar.baz')
        self.assertEqual('baz', self.app.request.path[1])

        self.app.router.add('/foo.bar/boz', None)
        self.make_request('/foo.bar/boz.baz')
        self.assertEqual('baz', self.app.request.path[1])

    def it_should_parse_GET_params_correctly(self):
        self.app.router.add('/', None)
        self.make_request('/', qs='a=1&b[]=2&b[]=3&baz=true&b=4&b[foo]=bar')

        params = {
            'a': 1,
            'b': {0: 2, 1: 3, 2: 4, 'foo': 'bar'},
            'baz': True
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
        routes = {
            '/:foo': {
                '/meh': {
                    'foo': 'meh'
                    },
                '/blah': {
                    'foo': 'blah'
                    }
                },
            '/company/:dept[/:name]': {
                '/company/it': {
                    'dept': 'it'
                    },
                '/company/it/support': {
                    'dept': 'it',
                    'name': 'support'
                    },
                }
            }

        for route, requests in routes.iteritems():
            self.app.router.add(route, None)

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
            ('/', '.xml', index, '<?xml version=\'1.0\' encoding=\'UTF-8\'?><response route="/" request="/" method="get">index</response>'),
            ('/foo', '.xml', foo, '<?xml version=\'1.0\' encoding=\'UTF-8\'?><response route="/foo" request="/foo" method="get">  <a nodetype="boolean">true</a>  <b nodetype="boolean">false</b></response>'),
            )

        for route, ext, func, body in routes:
            self.app.router.add(route, func)

        for route, ext, func, body in routes:
            self.assertBody(body, route+ext)


class PostRequestSpec(WSGITestBase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.app.config.format['xsl'] = {
            'stylesheet_path': 'specs',
            'default_stylesheet': 'translated_response_spec.xsl',
            }

    def it_should_parse_post_params_correctly(self):
        self.app.router.add('/', None, methods='GET,POST')
        self.make_request('/', method='POST', qs='a=1&b[]=2&b[]=3&baz=true&b=4&b[foo]=bar')

        params = {
            'a': 1,
            'b': {0: 2, 1: 3, 2: 4, 'foo': 'bar'},
            'baz': True
            }

        for key, value in params.iteritems():
            self.assert_(key in self.app.request['POST'])
            self.assertEqual(value, self.app.request['POST'][key])


    """
    def it_should_parse_multipart_posts_correctly(self):
        self.fail('Not yet implemented)

    def ensure_get_does_not_clobber_post_params(self):
        self.fail('Not yet implemented)

    def it_should_not_allow_incorrect_content_length(self):
        self.fail('Not yet implemented)

    """

