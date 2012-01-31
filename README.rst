FWRD -- FrameWork, Re-Done
==========================

DESCRIPTION
-----------

FWRD is a microframework for Python which has been designed to 
"get out of the way" and simply provide enough to make an app
accessible from the web.

While FWRD has been used for production systems is still alpha 
software. Until it hits version 1.0 the api is subject to massive 
change/overhaul. Because of this we recommend that you use a
recent stable tag for production use, only using the ``HEAD`` for
evaluation and testing.

FEATURES
--------

- WSGI-compliant

- Simple routing with URL parameters, with support for advanced routing using regular expressions

- HTTP Method support for the "useful" (REST) methods: GET/POST/PUT/DELETE/HEAD

- Redirect support

- Automatic Response formatting: XSL-Translated output, XML, JSON, with more to follow. 

- Pluggable architecture: add your own response formatters, global and route-specific filters, WSGI modules

THINGS WE HAVEN'T IMPLEMENTED
-----------------------------

Templating
    We don't support templating using any of the common Python templating 
    libraries such as Jinja, Cheetah, Mako, etc. The default output format 
    is XML passed through an XSL stylesheet. Helpful formatters are available 
    so you can change the output to be JSON, YAML, etc. without any extra 
    "work"; just let your method return a standard Python type (dict, list, etc) 
    and it will be converted to something the browser can use. 

    However, if you really need to use an alternative formatter you can do
    so by creating a plugin for the ``Response``.

ORM
    We don't feel that we should dictate what database you use, so we don't
    supply an ORM. Feel free to use any of the popular ones, or an ODM, or 
    a flat-file database, or an in-memory database, or whatever persistance 
    you wish.

INSTALLATION & USAGE
--------------------

The quickest installation route is as follows:

    pip install http://github.com/unpluggd/FWRD/tarball/master

However, we recommend that you use buildout for all your applications:

``buildout.cfg`` file::
    
    [buildout]
    parts = server
    ...

    [server]
    recipe = zc.recipe.egg
    entry-points = server=server:main

``server.py`` file::

    from FWRD import *

    application.setup('webapp.cfg')

    def main():
        application.run()

``webapp.cfg`` file::

    Config:
      port: 8080
      formats:
        default: 'xsl'
        xsl:
          enabled: true
          stylesheet: 'xsl/default.xsl'
        xml:
          enabled: true
        json:
          enabled: true

    Routes:
      - route: /[index]

``xsl/default.xsl`` file::

    <?xml version="1.0" encoding="UTF-8"?>
    <xsl:stylesheet
       version="1.0"
       xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
       xmlns:fwrd="http://unplug.gd/FWRD"
       extension-element-prefixes="fwrd"
       exclude-result-prefixes="fwrd">

       <xsl:template match="response[@route='/[index]']">
         hello world
       </xsl:template>

     </xsl:stylesheet>

then from the command line::

    # python bootstrap.py 
    # ./bin/buildout
    # ./bin/server


PLANNED FEATURES / TO DO
------------------------

Please see the TODO_ document.

.. _TODO: //github.com/unpluggd/FWRD/blob/master/TODO.rst
