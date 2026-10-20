"""Command line interface for CloverConfigChecker.

Usage:
    clover-config-checker [options] <config.plist> [<config2.plist> ...]

Exit codes:
    0  all checked configs are valid (warnings are allowed)
    1  at least one config has validation errors (or --strict + warnings)
    2  usage / file / parse error
"""

import argparse
import os
import plistlib
import sys

from . import __version__
from .checker import (
    Checker, Issue, LEVEL_WARNING, find_duplicate_keys,
)
from .colors import paint, BOLD, GREEN, RED, YELLOW, use_color
from .report import print_compact_report, print_report, result_line

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_USAGE = 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='clover-config-checker',
        description='Validate Clover EFI config.plist files '
                    '(r515x+ schema), with fuzzy-match typo '
                    'suggestions.',
        epilog='Example: clover-config-checker EFI/CLOVER/config.plist')
    p.add_argument('configs', nargs='+', metavar='config.plist',
                   help='Clover config.plist file(s) to validate')
    p.add_argument('-q', '--quiet', action='store_true',
                   help='only print per-file Result lines and exit code')
    p.add_argument('-s', '--strict', action='store_true',
                   help='treat warnings as errors (exit 1)')
    p.add_argument('-v', '--verbose', action='store_true',
                   help='show the verified-section listing (default)')
    p.add_argument('-b', '--brief', action='store_true',
                   help='hide the verified-section listing (minimal output)')
    p.add_argument('--build', action='store_true',
                   help='build-mode checks for the shipped '
                        'config-sample.plist: suppress the "?"-suffix '
                        'documentation note (the stock sample '
                        'intentionally carries ~128 of them)')
    p.add_argument('--oneline', action='store_true',
                   help='collapse the report to one line per file '
                        '(build-log style: no checklist, no summary '
                        'block; problems are indented under the header)')
    p.add_argument('--color', choices=('auto', 'always', 'never'),
                   default='auto', metavar='WHEN',
                   help='colourise output: auto (default), always, never')
    p.add_argument('--version', action='version',
                   version='clover-config-checker %s' % __version__)
    return p


def check_file(path: str, build_mode: bool = False):
    """Check one file.

    Returns (issues, hard_error_message or None, parsed config or None).
    """
    try:
        with open(path, 'rb') as f:
            raw = f.read()
    except OSError as e:
        return [], 'cannot read file: %s' % e.strerror, None

    try:
        config = plistlib.loads(raw)
    except plistlib.InvalidFileException:
        return [], 'not a valid plist file (XML or binary expected)', None
    except Exception as e:  # malformed XML etc.
        return [], 'plist parse error: %s' % e, None

    issues = Checker(build_mode=build_mode).check(config)

    # Duplicate keys: plistlib keeps only the last value, so scan raw XML.
    dup = find_duplicate_keys(raw)
    for dpath, dkey in dup:
        loc = dpath if dpath else 'root'
        issues.append(Issue(
            LEVEL_WARNING, loc or path,
            "duplicate key '%s' -- the last occurrence silently wins"
            % dkey))
    return issues, None, config


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    color = use_color(mode=args.color)

    if not args.configs:
        print('Error: no config file given', file=sys.stderr)
        return EXIT_USAGE

    total_errors = 0
    total_warnings = 0
    saw_hard_error = False

    for path in args.configs:
        issues, hard_error, config = check_file(path,
                                                build_mode=args.build)
        if hard_error is not None:
            saw_hard_error = True
            if args.oneline:
                print(paint('CloverConfigChecker: %s -- %s'
                            % (os.path.basename(path), hard_error),
                            RED, enabled=color))
            elif not args.quiet:
                print('Validating %s ...' % path)
                print(paint('Error: %s' % hard_error, RED, enabled=color))
                print()
            continue

        errors = sum(1 for i in issues if i.level == 'ERROR')
        warnings = sum(1 for i in issues if i.level == LEVEL_WARNING)

        if args.quiet:
            verdict = result_line(errors, warnings).replace('Result: ', '')
            if color:
                codes = (BOLD, RED) if errors else \
                    ((YELLOW,) if warnings else (BOLD, GREEN))
                verdict = paint(verdict, *codes)
            print('%s: %s' % (path, verdict))
        elif args.oneline:
            print_compact_report(path, issues, color=color, config=config)
        else:
            print_report(path, issues, quiet=False, color=color,
                         config=config, verbose=not args.brief,
                         build_mode=args.build)

        if args.strict:
            # warnings become errors; report still shows original levels
            total_errors += errors + warnings
        else:
            total_errors += errors
            total_warnings += warnings

    if saw_hard_error:
        return EXIT_USAGE
    if args.strict and total_warnings:
        return EXIT_INVALID
    if total_errors:
        return EXIT_INVALID
    return EXIT_OK


if __name__ == '__main__':
    sys.exit(main())
