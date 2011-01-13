To Do
=====

- v0.2.*:

  - Built-in Logging

  - Per-Formatter options/config

  - Server-side browser "sniffing", based on `Modernizr`_, for use with the XSL formatter

- Other Features

  - Decorator to "clean" data from return value::
  
      @response.trim(dotted-str)
  
  - Decorator to apply callbacks to response value::
  
      @response.apply(fn)

  - Auto-reloading of code on file modification

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

  - Add ``sendfile`` func which is compatible with Nginx X-Accel headers::
  
      response.sendfile(filename, data,
                        content_type="application/octet-stream",
                        force_download=True # Content-Disposition: attachment;
                        ) 

  - XML

    - allow creating of processing instructions using the following format:: 
    
        {"?xml-stylesheet": {'type':'', 'href':''}}
        
  - XSL
  
    - caching of "compiled" XSL files 

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

    - implode

    - in

    - starts-with

    - ends-with

    - matches

    - tokenize

    - exists?

    - distinct (values)

    - unique (nodes)

    - reverse

  - Decorators:

    - ``@response.format('type', **params)`` to change default formatter for function

TBC
---

Local fall-back for sessions when beaker isn't available?

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
