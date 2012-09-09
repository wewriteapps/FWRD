import os
import re
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from http_spec import WSGITestBase

FWRD_PATH = '/'.join(os.path.dirname(os.path.abspath(__file__)).split('/')[0:-1])

if FWRD_PATH not in sys.path:
    sys.path.insert(1, FWRD_PATH)

from FWRD import *


class NotFoundRequestSpec(WSGITestBase):
    '''404 NotFound request spec'''

    def setUp(self):
        super(self.__class__, self).setUp()

    def it_should_format_routing_errors_correctly(self):
        self.assertStatus(404, '/unknown_path.xml')
        '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="__not_found__" request="/unknown_path" method="get">
  <node name="__message__">routing failed for "/unknown_path" using method GET</node>
  <node name="__error__">404</node>
  <node name="__request_path__">/unknown_path.xml</node>
  <node name="__http_method__">GET</node>
</response>
'''
        self.assertXPath({
            '/response/@route': '__not_found__',
            '/response/@request': '/unknown_path',
            '/response/node[@name="__message__"]': 'routing failed for "/unknown_path" using method GET',
            '/response/node[@name="__error__"]': '404',
            '/response/node[@name="__request_path__"]': '/unknown_path.xml',
            '/response/node[@name="__http_method__"]': 'GET',
            }, route='/unknown_path.xml')


    def it_should_format_raised_errors_correctly(self):
        def raises(): raise NotFound()
        self.app.router.add('/raises', raises)
        self.assertStatus(404, '/raises.xml')
        '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/raises" request="/raises" method="get">
  <node name="__message__">routing failed for "/raises" using method GET</node>
  <node name="__error__">404</node>
  <node name="__request_path__">/raises.xml</node>
  <node name="__http_method__">GET</node>
</response>
'''

        self.assertXPath({
            '/response/@route': '/raises',
            '/response/@request': '/raises',
            '/response/node[@name="__message__"]': 'routing failed for "/raises" using method GET',
            '/response/node[@name="__error__"]': '404',
            '/response/node[@name="__request_path__"]': '/raises.xml',
            '/response/node[@name="__http_method__"]': 'GET',
            }, route='/raises.xml')



class RedirectSpec(WSGITestBase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.app.config.formats['xsl'] = {
            'stylesheet_path': '.',
            'default_stylesheet': 'translated_response_spec.xsl',
            }

    def it_should_set_correct_Redirect_headers(self):
        def bounce(): raise Redirect('/')
        self.app.router.add('/bounce', bounce)
        self.assertStatus(307, '/bounce.xml')
        '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<response route="/bounce" request="/bounce" method="get"/>'''

        self.assertXPath({
            '/response/@route': '/bounce',
            '/response/@request': '/bounce',
            }, route='/bounce.xml')


    def it_should_set_correct_SeeOther_headers(self):
        def bounce(): raise SeeOther('/')
        self.app.router.add('/seeother', bounce)
        self.assertStatus(303, '/seeother.xml')
        '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<response route="/seeother" request="/seeother" method="get"/>'''

        self.assertXPath({
            '/response/@route': '/seeother',
            '/response/@request': '/seeother',
            }, route='/seeother.xml')


    def it_should_set_correct_Moved_headers(self):
        def bounce(): raise Moved('/')
        self.app.router.add('/moved', bounce)
        self.assertStatus(301, '/moved.xml')
        '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<response route="/moved" request="/moved" method="get"/>'''

        self.assertXPath({
            '/response/@route': '/moved',
            '/response/@request': '/moved',
            }, route='/moved.xml')



class MethodArgsErrorSpec(WSGITestBase):
    '''Method-arguments error spec'''
    def setUp(self):
        super(self.__class__, self).setUp()
        self.app.config.formats['xsl'] = {
            'stylesheet_path': '.',
            'default_stylesheet': 'translated_response_spec.xsl',
            }

    def it_should_fail_when_passed_unexpected_args(self):
        def foo(): pass
        self.assertRaises(RouteCompilationError,
                          self.app.router.add,
                          '/foo/:bar',
                          foo
                          )



    def it_should_report_missing_args(self):

        def missing(missing, param): pass
        self.assertRaises(RouteCompilationError,
                          self.app.router.add,
                          '/:missing',
                          missing
                          )


    def it_should_allow_kwargs(self):
        def bar(foo, **kwargs): pass
        self.app.router.add('/additional_params', bar)
        self.assertStatus(200, '/additional_params.xml', qs='foo=1&bar=2')
        '''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/additional_params" request="/additional_params" method="get">
  <content/>
  <errors/>
</response>
'''
        self.assertXPath({
            '/response/@route': '/additional_params',
            '/response/@request': '/additional_params',
            '/response/@method': 'get',
            '/response/content': None,
            '/response/errors': None,
            }, route='/additional_params.xml', qs='foo=1&bar=2')

