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

<xsl:variable name="a" />
<xsl:variable name="b" select="''" />

<xsl:template match="/">
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Empty Tests</title>
  </head>
  <body>
    <ul>
      <li><xsl:if test="fwrd:isempty(.)">true</xsl:if></li>
      <li><xsl:if test="fwrd:isempty($a)">true</xsl:if></li>
      <li><xsl:if test="fwrd:isempty($b)">true</xsl:if></li>
      <li><xsl:if test="fwrd:isempty('')">true</xsl:if></li>
    </ul>
  </body>
</html>
</xsl:template>

</xsl:stylesheet>