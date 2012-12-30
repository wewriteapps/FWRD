To Do
=====

- Modularise

  - Move the XPath functions into a new python module

- v0.2.*:

  - Add configurable output logging to start-up & request/response cycle

  - Per-Formatter options/config

  - Server-side browser "sniffing", based on `Modernizr`_, for use with the XSL formatter

- Other Features

  - Decorators:

    - change/force formatter for function::
        
        @response.format(type, **params)

    - "clean" data from return value::
  
        @response.trim(dotted-str)
  
    - apply callbacks to response value (handled with standard decorators?)::
  
        @response.apply(fn)

    - stream ``generator`` values as a response::

        @response.stream
        def fn():
            yield True

  - Auto-reloading of code on file modification (debugging option)

  - Option to output basic config file::

      # python -m FWRD --example_config > webapp.cfg

  - `XSRF`_ validation, similar to that from `tornado`_

  - lift-/seaside-based form handling: 

    - each browser tab can have/has it's own session

    - forms can be secured with unique key in "action" url::
    
        <form action="{fwrd:register-form('/path/to/action')}" method="post">
        ...
        </form>

  - auto-creation of caching decorator when beaker-cache is available

  - InternalRedirect exception to restart the request with new data but respond to original query::

      InteralRedirect(url, method='GET', params={}, replace_params=False)

  - Parameter "type" for working with both string and native parameters

  - base64 encoding of binary data in output, using the data-uri format.

  - Add ``sendfile`` func/decorator which is compatible with Nginx X-Accel headers::
  
      response.sendfile(filename, data,
                        content_type="application/octet-stream",
                        force_download=True # Content-Disposition: attachment;
                        ) 

  - Add object to aid unittesting for devs (similar to Flask)

  - Flask Flashing?

  - XSL
  
    - toggle "caching" of "compiled" XSL files

  - XPath function implementations:

    - abs

    - ceiling

    - floor

    - avg

    - min

    - max

    - round

    - round-half-to-even

    - compare

    - any(test, (els))?

    - all(test, (els))?

    - concat

    - in

    - starts-with

    - ends-with

    - matches

    - tokenize

    - exists?

    - distinct (values)

    - unique (nodes)

    - reverse

TBC
---

How should authentication be handled? `AuthKit`_? Custom? None (handled by developer)?

``define`` and ``defined``, from `tornado`_?

Keep a log of the last request's (or last few requests'?) information (request, params, session, etc) to be raised when an error/exception is thrown.

.. _tornado: http://github.com/facebook/tornado
.. _beaker: http://beaker.groovie.org
.. _AuthKit: http://authkit.org
.. _webob: http://pythonpaste.org/webob
.. _bottle: http://github.com/defnull/bottle
.. _XPath Callbacks: http://codespeak.net/lxml/extensions.html#xpath-extension-functions
.. _XSRF: http://en.wikipedia.org/wiki/Cross-site_request_forgery
.. _Modernizr: http://modernizr.com
.. _generator: http://codedstructure.blogspot.com/2010/12/http-streaming-from-python-generators.html
