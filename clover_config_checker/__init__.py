"""CloverConfigChecker -- validate Clover EFI config.plist files.

An original, pure-Python tool for the Clover bootloader, written from
scratch: schema-driven validation, enum/range/format checks, fuzzy-match
typo suggestions and a grep-friendly plain-text report. The schema is
derived exclusively from Clover's own official config-sample.plist and
Clover documentation.
"""

__version__ = '1.8.3'
