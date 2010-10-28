YAML formatting for set-up:
===========================

Config:
  port: 8001

Formats:
  default: XSL
  XSL:
    enabled: Yes
    stylesheet_path: xsl
    default_stylesheet: default.xsl
  XML:
    enabled: Yes
  JSON:
    enabled: Yes

Routes:
  - url: /[index]
    callable: None
    methods: [GET, POST] # GET by default
    filters: [capture_brand, clear_session]
    formats: [XSL,XML,JSON] # All enabled formatters are allowed by default
  - url: /help
    callable: class.method # must be available from the main script
