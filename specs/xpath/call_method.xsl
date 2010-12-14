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

<xsl:template match="/">
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Call-Method Spec</title>
  </head>
  <body>
    <h1>Simple Calls</h1>
    <dl>
      <dt>String</dt>
        <dd><xsl:copy-of select="fwrd:call-method('specs.xpath.call:string_test')" /></dd>
	<dd><xsl:value-of select="fwrd:call-method('specs.xpath.call:string_test')" /></dd>
      <dt>List</dt>
        <dd><xsl:copy-of select="fwrd:call-method('specs.xpath.call:list_test')" /></dd>
	<dd><xsl:value-of select="fwrd:call-method('specs.xpath.call:list_test')/i[1]" /></dd>
	<dd><xsl:value-of select="fwrd:call-method('specs.xpath.call:list_test')/i[2]" /></dd>
      <dt>Tuple</dt>
        <dd><xsl:copy-of select="fwrd:call-method('specs.xpath.call:tuple_test')" /></dd>
	<dd><xsl:value-of select="fwrd:call-method('specs.xpath.call:tuple_test')/i[1]" /></dd>
	<dd><xsl:value-of select="fwrd:call-method('specs.xpath.call:tuple_test')/i[2]" /></dd>
      <dt>Dict</dt>
        <dd><xsl:copy-of select="fwrd:call-method('specs.xpath.call:dict_test')" /></dd>
	<dd><xsl:value-of select="fwrd:call-method('specs.xpath.call:dict_test')/spam" /></dd>
      <dt>Object</dt>
        <dd><xsl:copy-of select="fwrd:call-method('specs.xpath.call:object_test')" /></dd>
	<dd><xsl:value-of select="fwrd:call-method('specs.xpath.call:object_test')/PlainObject/spam" /></dd>
    </dl>
    <h1>Advanced Calls</h1>
    <dl>
      <dt>Accepts Args</dt>
        <dd><xsl:copy-of select="fwrd:call-method('specs.xpath.call:arg_test', 'spam=eggs')/text()" /></dd>
      <dt>No Args</dt>
        <dd><xsl:copy-of select="fwrd:call-method('specs.xpath.call:noarg_test', 'spam=eggs')/text()" /></dd>
    </dl>
  </body>
</html>
</xsl:template>

</xsl:stylesheet>
