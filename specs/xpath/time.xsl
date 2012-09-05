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
    <title>Format a Time</title>
  </head>
  <body>
    <xsl:variable name="t" select="'2010-01-01T00:00.00'" />
    <ul>
      <li><xsl:value-of select="fwrd:timeformat('2010-01-01', '%b %d, %Y')" /></li>
      <li><xsl:value-of select="fwrd:timeformat('2010-01-01T16:47Z', '%H:%M:%S %b %d, %Y')" /></li>
      <li><xsl:value-of select="fwrd:timeformat('16:47', '%H:%M:%S')" /></li>
      <li><xsl:value-of select="fwrd:timeformat('2010-01-01T16:47Z', '%H:%M:%S %b %d, %Y', 'Europe/Rome')" /></li>
      <li><xsl:value-of select="fwrd:timeformat('2010-01-01T00:00Z', '%H:%M:%S %b %d, %Y', 'America/New_York')" /></li>
      <li><xsl:value-of select="fwrd:timeformat('2010-01-01T00:00', '%H:%M:%S %b %d, %Y', 'America/New_York')" /></li>
      <li><xsl:value-of select="fwrd:format-time(str:split($t, '.')[1], '%A %B %_d, %Y at %_I:%M%p', 'Europe/London')" /></li>
    </ul>
  </body>
</html>
</xsl:template>

</xsl:stylesheet>
