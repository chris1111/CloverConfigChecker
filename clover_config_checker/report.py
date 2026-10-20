"""Output formatting for CloverConfigChecker.

Classic plain-text report, grep-friendly. By default every run ends
with a verified-section checklist so users can see exactly what was
checked:

    Validating config.plist ...
    ERROR: unknown key 'KextsToPatc' (similar to 'KextsToPatch') at KernelAndKextPatches
    WARNING: deprecated key -- renamed to GUI/Hide at GUI/HideVolume
    NOTE: 128 key(s) use the sample-file documentation suffix "?" ...

    Verified sections:
      Boot:                18 keys verified
      Quirks:              45 keys verified
      KernelAndKextPatches: 8 keys -- 1 error
      Total:               566 keys in 15 sections

    Summary: 2 errors, 1 warning, 1 note
    Result: INVALID -- 2 error(s) found

--brief hides the checklist for minimal output; --oneline collapses the
whole report into one build-log line:

    CloverConfigChecker: config-sample.plist -- 566 keys in 15 sections -- VALID

On a terminal the report is coloured (ERROR red, WARNING yellow, NOTE
cyan, verified sections green, VALID green) so the verdict is visible
at a glance; piped output stays plain unless --color always is given.
"""

import os
import sys

from .checker import LEVEL_ERROR, LEVEL_WARNING, LEVEL_NOTE
from .colors import paint, BOLD, DIM, RED, GREEN, YELLOW, CYAN, use_color

_ORDER = {LEVEL_ERROR: 0, LEVEL_WARNING: 1, LEVEL_NOTE: 2}


def _count_keys(value) -> int:
    """Recursively count leaf setting keys under a config value."""
    if isinstance(value, dict):
        return sum(_count_keys(v) for v in value.values())
    if isinstance(value, list):
        return sum(_count_keys(v) for v in value)
    return 1


def _plural(n: int, word: str) -> str:
    return '%d %s%s' % (n, word, 's' if n != 1 else '')


def _sec_counts(issues):
    """Coloured '(n errors, m warnings)' detail for a group of issues."""
    errs = sum(1 for i in issues if i.level == LEVEL_ERROR)
    warns = sum(1 for i in issues if i.level == LEVEL_WARNING)
    notes = sum(1 for i in issues if i.level == LEVEL_NOTE)
    detail = ', '.join(_plural(n, w) for n, w in
                       ((errs, 'error'), (warns, 'warning'),
                        (notes, 'note')) if n)
    if errs:
        return detail, (BOLD, RED)
    if warns:
        return detail, (YELLOW,)
    return detail, (CYAN,)


def _fmt_sections(config, issues, color: bool, build_mode: bool = False):
    """One status line per top-level section (used by the full report).

    Green = verified clean, red/yellow/cyan = has errors/warnings/notes,
    dim = totals. Section names and count words stay intact so the
    output remains grep-friendly.
    In build_mode a documentation-suffix section ('DisableDrivers?')
    was validated against its base key's schema entry, so it is shown
    under its clean base name exactly like every other section -- one
    uniform checklist in the build log. Manual runs keep the
    educational 'inert' tag.
    """
    by_sec = {}
    for issue in issues:
        top = (issue.path or '').split('/')[0]
        if top == 'root':
            top = ''
        by_sec.setdefault(top, []).append(issue)

    lines = []
    names = [n for n in config if not str(n).startswith('#')]
    width = max([len(str(n)) for n in names] + [len('Total')])

    def row(label, text, *codes):
        padded = ('%s:' % label).ljust(width + 1)
        lines.append('  ' + paint('%s %s' % (padded, text), *codes,
                                  enabled=color))

    total_keys = 0
    for name in config:
        sname = str(name)
        if sname.startswith('#'):
            continue
        nkeys = _count_keys(config[name])
        total_keys += nkeys
        if sname.endswith('?'):
            if build_mode:
                # Build log: the '?' suffix is the sample file's own
                # documentation convention, and this section's contents
                # were validated against the base key's schema entry --
                # so show it under its clean base name, like every
                # other section, for one uniform checklist.
                sec = by_sec.pop(sname, [])
                if sec:
                    detail, codes = _sec_counts(sec)
                    row(sname[:-1],
                        '%s -- %s' % (_plural(nkeys, 'key'), detail),
                        *codes)
                else:
                    row(sname[:-1],
                        '%s verified' % _plural(nkeys, 'key'), GREEN)
            else:
                row(sname, '%s -- %s' % (
                    _plural(nkeys, 'key'),
                    'inert (Clover ignores "?" keys)'), DIM)
            continue
        sec = by_sec.pop(sname, [])
        if sec:
            detail, codes = _sec_counts(sec)
            row(sname, '%s -- %s' % (_plural(nkeys, 'key'), detail), *codes)
        else:
            row(sname, '%s verified' % _plural(nkeys, 'key'), GREEN)

    root = by_sec.pop('', [])
    if root:
        detail, codes = _sec_counts(root)
        row('(root)', detail, *codes)
    row('Total', '%s in %s' % (_plural(total_keys, 'key'),
                               _plural(len(names), 'section')), DIM)
    return lines

_LEVEL_STYLE = {
    LEVEL_ERROR: (BOLD, RED),
    LEVEL_WARNING: (YELLOW,),
    LEVEL_NOTE: (CYAN,),
}


def _fmt_issue(issue, color: bool) -> str:
    """Plain issue.format(), or severity-coloured when enabled."""
    if not color:
        return issue.format()
    codes = _LEVEL_STYLE.get(issue.level, ())
    body = '%s: %s' % (paint(issue.level, *codes), issue.message)
    if issue.path:
        body += ' at %s' % paint(issue.path, DIM)
    return body


def _fmt_result(result: str, color: bool) -> str:
    if not color:
        return result
    if result.startswith('Result: INVALID'):
        return paint(result, BOLD, RED)
    if result.startswith('Result: VALID with warnings'):
        return paint(result, YELLOW)
    return paint(result, BOLD, GREEN)


def _fmt_summary(errors: int, warnings: int, notes: int, color: bool) -> str:
    def part(n, word):
        txt = '%d %s%s' % (n, word, 's' if n != 1 else '')
        if not color or n == 0:
            return txt
        if word == 'error':
            return paint(txt, RED)
        if word == 'warning':
            return paint(txt, YELLOW)
        return paint(txt, CYAN)
    line = 'Summary: %s' % ', '.join((part(errors, 'error'),
                                      part(warnings, 'warning'),
                                      part(notes, 'note')))
    if color and errors == 0 and warnings == 0 and notes == 0:
        return paint(line, BOLD, GREEN)   # all-clear glow
    return line


def print_report(fname: str, issues, quiet: bool = False,
                 color: bool = None, config=None,
                 verbose: bool = True,
                 build_mode: bool = False) -> None:
    """Print all issues for one file plus its summary block.

    `color` True/False forces the mode; None auto-detects the terminal.
    `verbose` (default True) lists every top-level section with its
    verified key count (requires the parsed `config`); the CLI hides
    the listing with --brief, and --quiet suppresses it anyway.
    `build_mode` renders '?'-suffix documentation sections like any
    other section (the '?'-suffix NOTE is already suppressed by the
    Checker itself), keeping the build-log checklist uniform.
    """
    if color is None:
        color = use_color()
    if not quiet:
        print(paint('Validating %s ...' % fname, DIM, enabled=color))
    for issue in sorted(issues,
                        key=lambda i: (_ORDER.get(i.level, 9), i.path)):
        print(_fmt_issue(issue, color))

    if verbose and not quiet and isinstance(config, dict):
        print()
        print(paint('Verified sections:', DIM, enabled=color))
        for line in _fmt_sections(config, issues, color,
                                  build_mode=build_mode):
            print(line)

    errors = sum(1 for i in issues if i.level == LEVEL_ERROR)
    warnings = sum(1 for i in issues if i.level == LEVEL_WARNING)
    notes = sum(1 for i in issues if i.level == LEVEL_NOTE)

    if not quiet:
        print()
        print(_fmt_summary(errors, warnings, notes, color))
        if errors:
            result = 'Result: INVALID -- %d error(s) found' % errors
        elif warnings:
            result = 'Result: VALID with warnings'
        else:
            result = 'Result: VALID'
        print(_fmt_result(result, color))
        print()


def result_line(errors: int, warnings: int) -> str:
    if errors:
        return 'Result: INVALID -- %d error(s) found' % errors
    if warnings:
        return 'Result: VALID with warnings'
    return 'Result: VALID'


def print_compact_report(fname: str, issues, color: bool = None,
                         config=None) -> None:
    """One-line-per-file report for build logs (CLI --build flag).

    A clean config collapses to a single confident line that matches the
    terse style of the rest of the Clover build log:

        CloverConfigChecker: config-sample.plist -- 566 keys in 15 sections -- VALID

    Problems are printed as indented issue lines directly under the same
    header -- no banner, no section checklist, no summary block, so the
    build log stays quiet unless something genuinely needs attention.
    """
    if color is None:
        color = use_color()
    base = os.path.basename(fname)

    errors = sum(1 for i in issues if i.level == LEVEL_ERROR)
    warnings = sum(1 for i in issues if i.level == LEVEL_WARNING)
    notes = sum(1 for i in issues if i.level == LEVEL_NOTE)

    parts = [txt for txt, n in (
        (_plural(errors, 'error'), errors),
        (_plural(warnings, 'warning'), warnings),
        (_plural(notes, 'note'), notes)) if n]
    detail = ', '.join(parts)

    if errors:
        verdict, codes = 'INVALID', (BOLD, RED)
    elif warnings:
        verdict, codes = 'VALID with warnings', (YELLOW,)
    else:
        verdict, codes = 'VALID', (BOLD, GREEN)
    if detail:
        verdict += ' (%s)' % detail

    header = 'CloverConfigChecker: %s -- ' % base
    if isinstance(config, dict):
        names = [n for n in config if not str(n).startswith('#')]
        total_keys = sum(_count_keys(config[n]) for n in names)
        header += '%s in %s -- ' % (_plural(total_keys, 'key'),
                                    _plural(len(names), 'section'))
    header += verdict
    print(paint(header, *codes, enabled=color))

    for issue in sorted(issues,
                        key=lambda i: (_ORDER.get(i.level, 9), i.path)):
        print('  ' + _fmt_issue(issue, color))
