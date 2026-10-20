"""Validation engine for CloverConfigChecker.

Walks a parsed config.plist against the schema and collects Issue objects:

  ERROR    - broken structure: unknown keys, wrong types, bad hex/UUID,
             unknown strict enum values, missing/empty required sections
  WARNING  - suspicious but possibly intentional: out-of-range numbers,
             unknown lenient enum values, Find/Replace length mismatch,
             deprecated keys
  NOTE     - informational hints (e.g. sample-file '?' suffixes)
"""

import re
from typing import List, Optional

from . import schema as sc
from . import schema_clover as cl
from .fuzzy import similar, format_suggestions

LEVEL_ERROR = 'ERROR'
LEVEL_WARNING = 'WARNING'
LEVEL_NOTE = 'NOTE'

_DEC_RE = re.compile(r'^-?[0-9]+$')
_HEXNUM_RE = re.compile(r'^(0[xX][0-9A-Fa-f]+|[0-9]+)$')

# plistlib maps XML <data> to bytes; other unexpected python types map back
# to plist type names for messages.
_PLIST_TYPE_NAMES = {
    str: 'string', int: 'integer', float: 'real', bool: 'boolean',
    bytes: 'data', list: 'array', dict: 'dict',
}


def plist_type_name(value) -> str:
    if isinstance(value, bool):          # before int: bool is an int subclass
        return 'boolean'
    for pytype, name in _PLIST_TYPE_NAMES.items():
        if isinstance(value, pytype):
            return name
    return type(value).__name__


class Issue:
    __slots__ = ('level', 'path', 'message')

    def __init__(self, level: str, path: str, message: str):
        self.level = level
        self.path = path
        self.message = message

    def format(self) -> str:
        if self.path:
            return '%s: %s at %s' % (self.level, self.message, self.path)
        return '%s: %s' % (self.level, self.message)


class Checker:
    def __init__(self, build_mode: bool = False):
        self.issues: List[Issue] = []
        self._qmark_hits: List[str] = []   # '?'-suffixed key paths
        # build_mode: validating the shipped config-sample.plist inside a
        # Clover build. The '?'-suffixed documentation keys are the
        # intended state there, so the long educational NOTE is
        # suppressed and the sample validates a clean 0/0/0.
        self.build_mode = build_mode

    # ---------------------------------------------------------------- API

    def check(self, config) -> List[Issue]:
        """Validate a parsed plist `config` (must be a dict at root)."""
        self.issues = []
        self._qmark_hits = []
        if not isinstance(config, dict):
            self._add(LEVEL_ERROR, '',
                      'root of config.plist must be a dict, found %s'
                      % plist_type_name(config))
            return self.issues
        if not config:
            self._add(LEVEL_ERROR, '',
                      'config.plist contains no settings (empty dict)')
            return self.issues
        self._check_required_sections(config)
        self._walk_dict(config, '', cl.ROOT_FIELDS, is_root=True)
        if self._qmark_hits and not self.build_mode:
            examples = ', '.join("'%s'" % p for p in self._qmark_hits[:5])
            more = '' if len(self._qmark_hits) <= 5 else \
                ' and %d more' % (len(self._qmark_hits) - 5)
            self._add(
                LEVEL_NOTE, '',
                '%d key(s) use the sample-file documentation suffix "?" '
                '(e.g. %s%s). This is normal for a stock install: the '
                'official Clover package installs config-sample.plist '
                'renamed as config.plist. Clover ignores "?"-suffixed '
                'keys, so these settings will NOT be applied -- remove '
                'the "?" suffix on a key to activate it'
                % (len(self._qmark_hits), examples, more))
        return self.issues

    # ------------------------------------------------------------ helpers

    def _add(self, level: str, path: str, message: str):
        self.issues.append(Issue(level, path, message))

    def _check_required_sections(self, config: dict):
        """Sections Clover itself refuses to boot without (e.g. Quirks)."""
        for req_name, req_msg in cl.REQUIRED_SECTIONS.items():
            if req_name not in config:
                hint = ''
                qmark = req_name + '?'
                if qmark in config:
                    hint = (" (found '%s' -- remove the trailing '?' "
                            'to activate it)' % qmark)
                self._add(LEVEL_ERROR, '',
                          "missing required section '%s' -- %s%s"
                          % (req_name, req_msg, hint))
            elif isinstance(config[req_name], dict) and not config[req_name]:
                self._add(LEVEL_ERROR, req_name,
                          'required section is empty -- %s' % req_msg)

    @staticmethod
    def _split_qmark(key: str):
        """Return (clean_name, had_qmark)."""
        if key.endswith('?'):
            return key[:-1], True
        return key, False

    def _type_mismatch(self, field: sc.Field, value, path: str):
        expected = ' or '.join(field.types)
        found = plist_type_name(value)
        self._add(LEVEL_ERROR, path,
                  "invalid type: expected %s, found %s%s"
                  % (expected, found,
                     ' -- %s' % field.value_note if field.value_note else ''))

    def _check_value(self, field: sc.Field, value, path: str):
        """Enum / pattern / range checks for scalar values."""
        if isinstance(value, bool):
            return
        if isinstance(value, int):
            if field.vmin is not None and value < field.vmin or \
               field.vmax is not None and value > field.vmax:
                lo = str(field.vmin) if field.vmin is not None else '-inf'
                hi = str(field.vmax) if field.vmax is not None else 'inf'
                self._add(LEVEL_WARNING, path,
                          'value %d out of expected range [%s, %s]'
                          % (value, lo, hi))
            return
        if isinstance(value, str):
            if field.enum is not None and value not in field.enum:
                sug = similar(value, field.enum)
                level = LEVEL_WARNING if field.enum_warn else LEVEL_ERROR
                self._add(level, path,
                          "unknown value '%s'%s -- expected one of: %s"
                          % (value, format_suggestions(sug),
                             ', '.join(field.enum)))
            if field.pattern is not None and value:
                if not re.match(field.pattern, value):
                    level = LEVEL_WARNING if field.pattern_warn \
                        else LEVEL_ERROR
                    self._add(level, path,
                              "value '%s' does not match expected format%s"
                              % (value, ' -- %s' % field.value_note
                                 if field.value_note else ''))
            return

    def _check_flex_specials(self, field: sc.Field, value, path: str):
        """Extra checks for flexible fields that accept int-or-string."""
        if isinstance(value, int):
            if field.vmin is not None and value < field.vmin or \
               field.vmax is not None and value > field.vmax:
                lo = str(field.vmin) if field.vmin is not None else '-inf'
                hi = str(field.vmax) if field.vmax is not None else 'inf'
                self._add(LEVEL_WARNING, path,
                          'value %d out of expected range [%s, %s]'
                          % (value, lo, hi))
            return
        if isinstance(value, str) and field.vmin is not None:
            # numeric strings like '5', '0x64' inside flexible fields
            if _DEC_RE.match(value):
                iv = int(value)
            elif _HEXNUM_RE.match(value):
                iv = int(value, 0)
            else:
                return
            if field.vmin is not None and iv < field.vmin or \
               field.vmax is not None and iv > field.vmax:
                lo = str(field.vmin) if field.vmin is not None else '-inf'
                hi = str(field.vmax) if field.vmax is not None else 'inf'
                self._add(LEVEL_WARNING, path,
                          'value %d out of expected range [%s, %s]'
                          % (iv, lo, hi))

    @staticmethod
    def _acceptable(field: sc.Field, value) -> bool:
        t = plist_type_name(value)
        if t in field.types:
            return True
        # Clover stores many numbers as hex/decimal strings
        if 'integer' in field.types and isinstance(value, str) and \
                (_DEC_RE.match(value) or _HEXNUM_RE.match(value)):
            return True
        return False

    # ------------------------------------------------------------- walkers

    def _walk_dict(self, node: dict, path: str,
                   fields: Optional[dict], is_root: bool = False):
        for key, value in node.items():
            key_path = '%s/%s' % (path, key) if path else key

            # Clover comment keys: '#' prefix, any content
            if key.startswith('#'):
                continue

            clean, had_qmark = self._split_qmark(key)

            # Deprecated exact path first (on cleaned name)
            dep_key = '%s/%s' % (path, clean) if path else clean
            if dep_key in cl.DEPRECATED and clean in (fields or {}):
                if had_qmark:
                    self._qmark_hits.append(key_path)
                self._add(LEVEL_WARNING, key_path,
                          'deprecated key -- %s' % cl.DEPRECATED[dep_key])
                continue
            if dep_key in cl.DEPRECATED:
                self._add(LEVEL_WARNING, key_path,
                          'deprecated key -- %s' % cl.DEPRECATED[dep_key])
                continue

            if fields is None:
                # free-form context
                if had_qmark:
                    self._qmark_hits.append(key_path)
                self._walk_any(value, key_path)
                continue

            if clean in fields:
                if had_qmark:
                    self._qmark_hits.append(key_path)
                self._walk_field(fields[clean], value, key_path)
                continue

            # Per-OS SMBIOS presets: SMBIOS_capitan, SMBIOS_ventura, ...
            if is_root and cl.is_smbios_preset(clean):
                self._walk_field(cl.smbios_preset_schema(), value, key_path)
                continue

            # Unknown key -> typo suggestions from sibling field names.
            # At root level also search one level deeper, so a whole-section
            # typo like 'KextPatches' can suggest 'KernelAndKextPatches'
            # or 'KernelAndKextPatches/KextsToPatch'.
            sug = similar(clean, fields.keys())
            if is_root:
                deeper = []
                for sname, sfield in fields.items():
                    if sfield.fields:
                        for child in sfield.fields:
                            deeper.append('%s/%s' % (sname, child))
                sug = list(sug) + similar(clean, deeper)
                sug = sug[:3]
            self._add(LEVEL_ERROR, key_path,
                      "unknown key%s" % format_suggestions(sug))

    def _walk_field(self, field: sc.Field, value, path: str):
        if not self._acceptable(field, value):
            self._type_mismatch(field, value, path)
            return

        types = plist_type_name(value)

        if types == sc.T_DICT:
            if field.free_form:
                return
            self._check_flex_specials(field, value, path)
            self._walk_dict(value, path, field.fields or {})
            return

        if types == sc.T_ARR:
            if field.item is not None:
                for i, elem in enumerate(value):
                    self._walk_field(field.item, elem,
                                     '%s[%d]' % (path, i))
            else:
                for i, elem in enumerate(value):
                    self._walk_any(elem, '%s[%d]' % (path, i))
            return

        # scalars
        if field.enum is not None or field.pattern is not None:
            self._check_value(field, value, path)
        else:
            self._check_flex_specials(field, value, path)

        # special case: ROM data should be 6 bytes
        if isinstance(value, bytes) and field.name == 'ROM' \
                and len(value) != 6:
            self._add(LEVEL_WARNING, path,
                      'ROM data should be exactly 6 bytes, found %d'
                      % len(value))

    def _walk_any(self, value, path: str):
        """Walk values whose schema is unknown (free-form containers)."""
        if isinstance(value, dict):
            self._walk_dict(value, path, None)
        elif isinstance(value, list):
            for i, elem in enumerate(value):
                self._walk_any(elem, '%s[%d]' % (path, i))


def validate(config) -> List[Issue]:
    """Convenience wrapper."""
    return Checker().check(config)


def find_duplicate_keys(xml_bytes: bytes) -> List[tuple]:
    """Scan raw XML plist for duplicate keys inside the same dict.

    plistlib silently keeps the last value, so hand-edited configs can
    hide contradictions. Returns a list of (dict_path, key) tuples.
    Only meaningful for XML plists; binary plists return no findings.
    """
    import xml.etree.ElementTree as ET

    results: List[tuple] = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return results

    top = root.find('dict') if root.tag == 'plist' else root
    if top is None:
        return results

    def walk(elem, path: str):
        if elem.tag == 'dict':
            children = list(elem)
            seen = set()
            for i in range(0, len(children) - 1, 2):
                k_el, v_el = children[i], children[i + 1]
                if k_el.tag != 'key':
                    continue
                ktext = k_el.text or ''
                if ktext in seen:
                    results.append((path, ktext))
                else:
                    seen.add(ktext)
                walk(v_el, '%s/%s' % (path, ktext) if path else ktext)
        elif elem.tag == 'array':
            for i, child in enumerate(list(elem)):
                walk(child, '%s[%d]' % (path, i))

    walk(top, '')
    return results
