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
    <title>Reverse Elements</title>
  </head>
  <body>
    <xsl:variable
       name="els"
       select="fwrd:string-to-fragment('&lt;items&gt;&lt;i&gt;a&lt;/i&gt;&lt;i&gt;b&lt;/i&gt;&lt;i&gt;c&lt;/i&gt;&lt;i&gt;d&lt;/i&gt;&lt;i&gt;e&lt;/i&gt;&lt;/items&gt;')/i"
       />
    <ul>
      <li><xsl:value-of select="fwrd:reverse('abcde')" /></li>
      <li><xsl:copy-of select="$els" /></li>
      <li><xsl:copy-of select="fwrd:reverse($els)" /></li>
    </ul>
  </body>
</html>
</xsl:template>

</xsl:stylesheet>
