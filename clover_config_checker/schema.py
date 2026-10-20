"""Schema primitives for CloverConfigChecker.

A schema is a tree of Field nodes describing the expected structure of a
Clover config.plist (r515x format). Each Field declares:

  - which plist value type(s) it accepts (boolean, integer, string, data,
    real, array, dict) -- Clover is famously lenient and accepts several
    forms for the same setting (e.g. hex strings like '0x64' for numeric
    values), so numeric helpers accept both.
  - optional enum values, regex pattern (for strings), numeric range
  - nested dict fields and/or array item schema
"""

import re
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, Pattern

# Canonical plist value types
T_BOOL = 'boolean'
T_INT = 'integer'
T_REAL = 'real'
T_STR = 'string'
T_DATA = 'data'
T_ARR = 'array'
T_DICT = 'dict'
T_ANY = 'any'

_UUID_RE = r'^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$'
_HEXNUM_RE = r'^(0[xX][0-9A-Fa-f]+|[0-9]+)$'          # 0x1F / 4026531840 / 31
_DEC_RE = r'^-?[0-9]+$'


@dataclass
class Field:
    """One key in the Clover config schema."""
    name: str
    types: Tuple[str, ...]
    fields: Optional[Dict[str, 'Field']] = None       # for dicts
    item: Optional['Field'] = None                    # for arrays
    enum: Optional[Tuple[str, ...]] = None            # allowed values (strings/ints as written)
    enum_warn: bool = False                           # unknown enum -> warning instead of error
    pattern: Optional[str] = None                     # regex for string values
    pattern_warn: bool = False                        # pattern miss -> warning instead of error
    vmin: Optional[int] = None
    vmax: Optional[int] = None
    free_form: bool = False                           # accept arbitrary nested content
    value_note: Optional[str] = None                  # extra guidance shown in messages


# --------------------------------------------------------------------------
# Field builder helpers
# --------------------------------------------------------------------------

def B(name: str, note: str = None) -> Field:
    """Plain boolean key."""
    return Field(name, (T_BOOL,), value_note=note)


def S(name: str, enum=None, enum_warn=False, pattern=None, pattern_warn=False,
      note: str = None) -> Field:
    """Plain string key."""
    return Field(name, (T_STR,), enum=enum, enum_warn=enum_warn,
                 pattern=pattern, pattern_warn=pattern_warn, value_note=note)


def DATA(name: str, note: str = None) -> Field:
    return Field(name, (T_DATA,), value_note=note)


def HEXNUM(name: str, vmin=None, vmax=None, note: str = None) -> Field:
    """Numeric setting: integer, or decimal/hex string ('0x64', '5')."""
    return Field(name, (T_INT, T_STR), vmin=vmin, vmax=vmax,
                 pattern=_HEXNUM_RE, pattern_warn=True, value_note=note)


def HEXSTR(name: str, note: str = None, warn=False) -> Field:
    """Hex-formatted string, e.g. FakeID '0x68181002'. Empty string allowed."""
    return Field(name, (T_STR, T_INT), pattern=r'^(0[xX][0-9A-Fa-f]*)?$',
                 pattern_warn=warn, value_note=note)


def UUID(name: str, note: str = None) -> Field:
    return Field(name, (T_STR,), pattern=_UUID_RE, value_note=note)


def NUM(name: str, vmin=None, vmax=None, note: str = None) -> Field:
    """Strictly numeric: integer or decimal string."""
    return Field(name, (T_INT, T_STR), vmin=vmin, vmax=vmax,
                 pattern=_DEC_RE, pattern_warn=True, value_note=note)


def STRNUM(name: str, vmin=None, vmax=None, note: str = None) -> Field:
    """Integer-typed setting that Clover stores as a string (e.g. '0xBFBFBF')."""
    return HEXNUM(name, vmin, vmax, note)


def DICT(name: str, fields: Dict[str, Field], note: str = None) -> Field:
    return Field(name, (T_DICT,), fields=fields, value_note=note)


def FREE(name: str, note: str = None) -> Field:
    """Free-form dict: contents are not validated (e.g. Devices/Properties)."""
    return Field(name, (T_DICT,), free_form=True, value_note=note)


def ARR(name: str, item: Field = None, note: str = None) -> Field:
    return Field(name, (T_ARR,), item=item, value_note=note)


def FLEX(name: str, types, fields=None, note: str = None, **extra) -> Field:
    """Setting that accepts multiple independent forms (dict|bool|string...).

    Extra keyword arguments (enum=..., vmin=..., ...) are applied to the
    underlying Field so flexible keys can still carry value constraints.
    """
    f = Field(name, tuple(types), fields=fields, value_note=note)
    for k, v in extra.items():
        setattr(f, k, v)
    return f


# --------------------------------------------------------------------------
# Shared sub-schemas
# --------------------------------------------------------------------------

def patch_item(name: str, extra_fields: Dict[str, Field] = None) -> Field:
    """Common structure of Find/Replace binary patch entries."""
    fields = {
        'Comment': S('Comment'),
        'Disabled': B('Disabled'),
        'Find': Field('Find', (T_DATA,)),
        'Replace': Field('Replace', (T_DATA,)),
        'MaskFind': Field('MaskFind', (T_DATA,)),
        'MaskReplace': Field('MaskReplace', (T_DATA,)),
        'MaskStart': Field('MaskStart', (T_DATA,)),
        'StartPattern': Field('StartPattern', (T_DATA,)),
        'RangeFind': NUM('RangeFind', vmin=0),
        'MatchOS': S('MatchOS'),
        'MatchBuild': S('MatchBuild'),
        'Procedure': S('Procedure'),
        'Count': NUM('Count', vmin=0),
        'Skip': NUM('Skip', vmin=0),
        'Limit': NUM('Limit', vmin=0),
    }
    if extra_fields:
        fields.update(extra_fields)
    return DICT(name, fields)
