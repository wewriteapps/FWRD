import os
import re
import sys
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

    def it_should_format_errors_correctly(self):
        self.assertStatus(404, '/unknown_path.xml')
        self.assertBody('''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="__not_found__" request="/unknown_path" method="get">
  <node name="__message__">routing failed when searching for "/unknown_path" using method GET</node>
  <node name="__error__">404</node>
  <node name="__request_path__">/unknown_path.xml</node>
  <node name="__http_method__">GET</node>
</response>
''', '/unknown_path.xml')



class RedirectSpec(WSGITestBase):

    def setUp(self):
        super(self.__class__, self).setUp()
        self.app.config.format['xsl'] = {
            'stylesheet_path': 'specs',
            'default_stylesheet': 'translated_response_spec.xsl',
            }

    def it_should_set_correct_Redirect_headers(self):
        def bounce(): raise Redirect('/')
        self.app.router.add('/bounce', bounce)
        self.assertStatus(307, '/bounce.xml')
        self.assertBody('<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<response route="/bounce" request="/bounce" method="get"/>', '/bounce.xml')

    def it_should_set_correct_SeeOther_headers(self):
        def bounce(): raise SeeOther('/')
        self.app.router.add('/seeother', bounce)
        self.assertStatus(303, '/seeother.xml')
        self.assertBody('<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<response route="/seeother" request="/seeother" method="get"/>', '/seeother.xml')

    def it_should_set_correct_Moved_headers(self):
        def bounce(): raise Moved('/')
        self.app.router.add('/moved', bounce)
        self.assertStatus(301, '/moved.xml')
        self.assertBody('<?xml version=\'1.0\' encoding=\'UTF-8\'?>\n<response route="/moved" request="/moved" method="get"/>', '/moved.xml')





class MethodArgsErrorSpec(WSGITestBase):
    '''Method-arguments error spec'''
    def setUp(self):
        super(self.__class__, self).setUp()
        self.app.config.format['xsl'] = {
            'stylesheet_path': 'specs',
            'default_stylesheet': 'translated_response_spec.xsl',
            }

    def it_should_fail_when_passed_unexpected_args(self):
        def foo(): pass
        self.assertRaises(RouteCompilationError,
                          self.app.router.add,
                          '/foo/:bar',
                          foo
                          )

        """
        self.app.config.debug = True
        self.assertStatus(403, '/foo/bar/baz.xml', qs='foo=1')
        self.assertBody('''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/index" request="/index" method="get">
  <node name="__message__">method "foo" takes no arguments</node>
  <node name="__error__">403</node>
  <node name="__request_path__">/index.xml</node>
  <node name="__http_method__">GET</node>
</response>
''', '/index.xml', qs='foo=bar')

        """

  
    def it_should_report_missing_args(self):

        def missing(missing, param): pass
        self.assertRaises(RouteCompilationError,
                          self.app.router.add,
                          '/:missing',
                          missing
                          )

        """
        self.assertStatus(403, '/missing.xml', qs='param=1')
        self.assertBody('''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/missing_params" request="/missing_params" method="get">
  <node name="__message__">method "missing" requires (foo, bar), missing (bar)</node>
  <node name="__error__">403</node>
  <node name="__request_path__">/missing_params.xml</node>
  <node name="__http_method__">GET</node>
</response>
''', '/missing_params.xml', qs='foo=1')
        """

    def it_should_allow_kwargs(self):
        def bar(foo, **kwargs): pass
        self.app.router.add('/additional_params', bar)
        self.assertStatus(200, '/additional_params.xml', qs='foo=1&bar=2')
        self.assertBody('''<?xml version=\'1.0\' encoding=\'UTF-8\'?>
<response route="/additional_params" request="/additional_params" method="get">
  <content/>
  <errors/>
</response>
''', '/additional_params.xml', qs='foo=1&bar=2')

