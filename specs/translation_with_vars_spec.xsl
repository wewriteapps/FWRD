<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet
   version="1.0"
   xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
   xmlns:re="http://exslt.org/regular-expressions"
   xmlns:date="http://exslt.org/dates-and-times"
   xmlns:random="http://exslt.org/random"
   xmlns:dyn="http://exslt.org/dynamic"
   xmlns:exsl="http://exslt.org/common"
   xmlns:str="http://exslt.org/strings"
   xmlns:math="http://exslt.org/math"
   xmlns:set="http://exslt.org/sets"
   xmlns:fwrd="http://fwrd.org/fwrd.extensions"
   extension-element-prefixes="fwrd re date random dyn exsl str math set"
   exclude-result-prefixes="fwrd re date random dyn exsl str math set">

<xsl:output
   version="5.0"
   method="html"
   encoding="UTF-8"
   omit-xml-declaration="yes"
   indent="yes"
   media-type="text/html"
   doctype-system=""
   doctype-public=""
   />

<xsl:variable
   name="_route"
   select="/response/@route"
   />

<xsl:variable
   name="_get"
   select="fwrd:params('GET')"
   />

<xsl:variable
   name="_post"
   select="fwrd:params('POST')"
   />

<xsl:variable
   name="_params"
   select="fwrd:params('PARAMS')"
   />

<xsl:variable
   name="_session"
   select="fwrd:session()"
   />

<xsl:template match="/">
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Basic HTML Response</title>
  </head>
  <body>
    <xsl:apply-templates />
  </body>
</html>
</xsl:template>

<xsl:template match="tuple">
  <ol>
    <xsl:for-each select="i">
      <li><xsl:value-of select="." /></li>
    </xsl:for-each>
  </ol>
</xsl:template>

</xsl:stylesheet>
