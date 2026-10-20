#!/usr/bin/env python3
"""Edge-case tests for CloverConfigChecker CLI."""
import plistlib
import shutil
import subprocess
import sys
import os
import tempfile

# Portable: this folder is wherever test_cli.py lives, so the suite works
# from any unpacked release zip on any machine.
CC = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(CC, 'samples')
TMP = os.path.join(tempfile.gettempdir(), 'clover_config_checker_tests')
shutil.rmtree(TMP, ignore_errors=True)
os.makedirs(TMP, exist_ok=True)


def run(*args):
    p = subprocess.run([sys.executable, '-m', 'clover_config_checker']
                       + list(args),
                       cwd=CC, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


fails = []


def expect(cond, label, extra=''):
    print(('PASS' if cond else 'FAIL'), label, extra if not cond else '')
    if not cond:
        fails.append(label)


# 1. duplicate key detection (XML with same key twice in one dict)
dup_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
    <key>Boot</key><dict>
        <key>Timeout</key><integer>5</integer>
        <key>Timeout</key><integer>99</integer>
    </dict>
    <key>GUI</key><dict><key>Theme</key><string>embedded</string></dict>
    <key>Quirks</key><dict><key>XhciPortLimit</key><false/></dict>
</dict></plist>'''
dup_path = os.path.join(TMP, 'dup.plist')
open(dup_path, 'w').write(dup_xml)
rc, out = run(dup_path)
expect(rc == 0, 'duplicate key -> warning only, exit 0', out)
expect("duplicate key 'Timeout'" in out, 'duplicate key message shown', out)

# 2. binary plist support
bin_path = os.path.join(TMP, 'binary.plist')
with open(bin_path, 'wb') as f:
    plistlib.dump({'Boot': {'Timeout': 5},
                   'Quirks': {'XhciPortLimit': False}},
                  f, fmt=plistlib.FMT_BINARY)
rc, out = run(bin_path)
expect(rc == 0 and 'VALID' in out, 'binary plist validates', out)

# 3. nonexistent file -> exit 2
rc, out = run(os.path.join(TMP, 'does-not-exist.plist'))
expect(rc == 2 and 'cannot read' in out, 'missing file -> exit 2', out)

# 4. garbage file -> exit 2
bad_path = os.path.join(TMP, 'garbage.plist')
open(bad_path, 'w').write('this is not a plist at all')
rc, out = run(bad_path)
expect(rc == 2, 'garbage file -> exit 2', out)

# 5. empty dict config -> error exit 1
empty_path = os.path.join(TMP, 'empty.plist')
with open(empty_path, 'wb') as f:
    plistlib.dump({}, f)
rc, out = run(empty_path)
expect(rc == 1 and 'no settings' in out, 'empty config -> error', out)

# 6. root not a dict -> error
arr_path = os.path.join(TMP, 'array.plist')
with open(arr_path, 'wb') as f:
    plistlib.dump([1, 2, 3], f)
rc, out = run(arr_path)
expect(rc == 1 and 'must be a dict' in out, 'array root -> error', out)

# 7. --strict makes warnings fatal
rc, out = run('--strict', os.path.join(SAMPLES, 'config-bad-types.plist'))
expect(rc == 1, 'strict mode -> warnings fatal, exit 1', out)

# 8. multiple files aggregate exit code
rc, out = run(os.path.join(SAMPLES, 'config-valid.plist'),
              os.path.join(SAMPLES, 'config-bad-typo.plist'))
expect(rc == 1, 'one bad file among good -> exit 1', out)

# 9. --version
rc, out = run('--version')
expect(rc == 0 and 'clover-config-checker' in out, '--version works', out)

# 10. SMBIOS preset sections accepted
smb_path = os.path.join(TMP, 'smbios_preset.plist')
with open(smb_path, 'wb') as f:
    plistlib.dump({
        'SMBIOS_capitan': {'ProductName': 'MacBookPro10,1', 'Trust': True},
        'SMBIOS_ventura': {'ProductName': 'MacBookPro15,4', 'Trust': False},
        'Quirks': {'XhciPortLimit': False},
    }, f)
rc, out = run(smb_path)
expect(rc == 0, 'SMBIOS_<os> presets accepted', out)

# 11. '#' comment keys accepted anywhere
hash_path = os.path.join(TMP, 'hash.plist')
with open(hash_path, 'wb') as f:
    plistlib.dump({
        '#Warning': 'read the docs',
        'KernelAndKextPatches': {
            '#ATIConnectorsData': '0004000004030000',
            'AppleRTC': True,
        },
        'Quirks': {'XhciPortLimit': False},
    }, f)
rc, out = run(hash_path)
expect(rc == 0, "'#' comment keys accepted", out)

# 12. bare '?'-suffixed known key -> aggregated note, not error
qm_path = os.path.join(TMP, 'qmark.plist')
with open(qm_path, 'wb') as f:
    plistlib.dump({'Boot': {'Timeout': 5, 'Fast?': False},
                   'Quirks': {'XhciPortLimit': False}}, f)
rc, out = run(qm_path)
expect(rc == 0 and '?' in out and 'NOTE' in out,
       "'?' suffix -> note + exit 0", out)

# 13. missing required Quirks section -> hard error
noq_path = os.path.join(TMP, 'no_quirks.plist')
with open(noq_path, 'wb') as f:
    plistlib.dump({'Boot': {'Timeout': 5}}, f)
rc, out = run(noq_path)
expect(rc == 1 and "missing required section 'Quirks'" in out,
       'missing Quirks -> error, exit 1', out)

# 14. present but empty Quirks -> hard error
emptyq_path = os.path.join(TMP, 'empty_quirks.plist')
with open(emptyq_path, 'wb') as f:
    plistlib.dump({'Quirks': {}}, f)
rc, out = run(emptyq_path)
expect(rc == 1 and 'required section is empty' in out,
       'empty Quirks -> error, exit 1', out)

# 15. only 'Quirks?' (sample-style) counts as missing, with hint
qmonly_path = os.path.join(TMP, 'qmark_quirks.plist')
with open(qmonly_path, 'wb') as f:
    plistlib.dump({'Quirks?': {'XhciPortLimit': False}}, f)
rc, out = run(qmonly_path)
expect(rc == 1 and "missing required section 'Quirks'" in out
       and 'remove the trailing' in out,
       "'Quirks?' only -> missing + rename hint", out)

# 16. piped output (auto colour) must stay plain -- no ANSI escapes
rc, out = run(noq_path)
expect(rc == 1 and '\x1b[' not in out,
       'piped output is plain (no ANSI codes)', out)

# 17. --color always forces ANSI codes even when piped
rc, out = run('--color', 'always', noq_path)
expect(rc == 1 and '\x1b[' in out and 'ERROR' in out,
       '--color always emits ANSI codes', out)

# 18. --color never suppresses ANSI codes
rc, out = run('--color', 'never', noq_path)
expect(rc == 1 and '\x1b[' not in out,
       '--color never suppresses ANSI codes', out)

# 19. NO_COLOR env wins in auto mode
env_path = os.path.join(TMP, 'no_color_env.plist')
import subprocess as _sp
p = _sp.run([sys.executable, '-m', 'clover_config_checker', noq_path],
            cwd=CC, capture_output=True, text=True,
            env=dict(os.environ, FORCE_COLOR='1', NO_COLOR='1'))
expect(p.returncode == 1 and '\x1b[' not in (p.stdout + p.stderr),
       'NO_COLOR overrides FORCE_COLOR in auto mode', p.stdout + p.stderr)

# 20. verified-section listing is shown by DEFAULT
rc, out = run(qm_path)
expect(rc == 0 and 'Verified sections:' in out and 'Boot:' in out
       and 'Quirks:' in out and 'verified' in out and 'Total:' in out,
       'default output lists verified sections + key counts', out)

# 21. --brief hides the section listing (minimal output)
rc, out = run('--brief', qm_path)
expect(rc == 0 and 'Verified sections:' not in out and 'Total:' not in out,
       '--brief hides the section listing', out)

# 22. default listing painted green with --color always
rc, out = run('--color', 'always', qm_path)
expect(rc == 0 and '\x1b[32m' in out,
       '--color always paints verified sections green', out)

# 23. top-level '?' sections marked inert + root issues row
rc, out = run(qmonly_path)
expect(rc == 1 and 'inert' in out and '(root)' in out,
       "'?' sections marked inert + root issues", out)

# 24. all-clean Summary line glows bold green with --color always
rc, out = run('--color', 'always', bin_path)   # bin_path = 0/0/0 config
expect(rc == 0 and '\x1b[1m\x1b[32mSummary: 0 errors' in out,
       'all-clean Summary glows bold green', out)

# 25. but a summary WITH issues does not glow green
rc, out = run('--color', 'always', noq_path)
expect(rc == 1 and '\x1b[1m\x1b[32mSummary' not in out,
       'summary with issues does not glow green', out)

# 26. build-hook wrapper (default): valid config -> full report, exit 0
import subprocess as sp2
hook = os.path.join(CC, 'run_config_check.sh')
p = sp2.run(['bash', hook, os.path.join(SAMPLES, 'config-valid.plist')],
            cwd=CC, capture_output=True, text=True)
expect(p.returncode == 0 and 'Result: VALID' in p.stdout
       and 'Verified sections:' in p.stdout
       and 'config.plist is valid' in p.stdout,
       'build hook: valid config -> full report + all-good, exit 0',
       p.stdout + p.stderr)

# 27. build hook is NON-FATAL by default even on invalid config
p = sp2.run(['bash', hook, os.path.join(TMP, 'no_quirks.plist')],
            cwd=CC, capture_output=True, text=True)
expect(p.returncode == 0 and 'Result: INVALID' in p.stdout
       and 'CHECKER_STRICT' in p.stdout,
       'build hook: invalid config -> warn only, build continues',
       p.stdout + p.stderr)

# 28. CHECKER_STRICT=1 makes the hook fail the build
p = sp2.run(['bash', hook, os.path.join(TMP, 'no_quirks.plist')],
            cwd=CC, capture_output=True, text=True,
            env=dict(os.environ, CHECKER_STRICT='1'))
expect(p.returncode == 1 and 'failing the build' in p.stdout,
       'build hook: CHECKER_STRICT=1 fails the build',
       p.stdout + p.stderr)

# 29. build-tree hook: no $1, config resolved from $CLOVER_PKG_DIR
#     (the build exports CLOVER_PKG_DIR=<CloverPackage>/CloverV2)
fake_v2 = os.path.join(TMP, 'fake_clover_pkg')
os.makedirs(os.path.join(fake_v2, 'EFI', 'CLOVER'), exist_ok=True)
shutil.copy(os.path.join(SAMPLES, 'config-valid.plist'),
            os.path.join(fake_v2, 'EFI', 'CLOVER', 'config-sample.plist'))
p = sp2.run(['bash', hook],
            cwd=CC, capture_output=True, text=True,
            env=dict(os.environ,
                     CLOVER_PKG_DIR=fake_v2,
                     CLOVER_CONFIG='', CHECKER_STRICT='1'))
expect(p.returncode == 0
       and os.path.join(fake_v2, 'EFI', 'CLOVER', 'config-sample.plist') in p.stdout
       and 'config.plist is valid' in p.stdout,
       'build hook: config auto-resolved from $CLOVER_PKG_DIR',
       p.stdout + p.stderr)

# 30. --oneline + --build (CLI): shipped sample collapses to ONE clean line
#     -- no checklist, no summary block, no '?' lecture, no inert tag
rc, out = run('--build', '--oneline',
              os.path.join(SAMPLES, 'clover-official-sample.plist'))
expect(rc == 0 and 'documentation suffix' not in out
       and 'Verified sections:' not in out and 'Summary:' not in out
       and '566 keys in 15 sections' in out and '-- VALID' in out,
       '--build --oneline: shipped sample -> one clean VALID line', out)

# 31. normal mode keeps the educational '?' note (no regression)
rc, out = run(os.path.join(SAMPLES, 'clover-official-sample.plist'))
expect(rc == 0 and 'documentation suffix' in out
       and 'Summary: 0 errors, 0 warnings, 1 note' in out,
       'normal mode keeps the ?-suffix note on the sample', out)

# 32. wrapper with an EXPLICITLY passed config -> MANUAL mode: the
#     standard user report, identical to the CLI (a stock
#     config-sample.plist from the source tree shows the '?'-note)
p = sp2.run(['bash', hook,
             os.path.join(SAMPLES, 'clover-official-sample.plist')],
            cwd=CC, capture_output=True, text=True)
expect(p.returncode == 0 and 'documentation suffix' in p.stdout
       and 'Summary: 0 errors, 0 warnings, 1 note' in p.stdout
       and 'Verified sections:' in p.stdout
       and 'config.plist is valid' in p.stdout,
       'wrapper + explicit config -> manual user report (with ?-note)',
       p.stdout + p.stderr)

# 32b. wrapper + CHECKER_BUILD=1 -> build mode on an explicit path
#      (clean 0/0/0 full report, '?'-note suppressed)
p = sp2.run(['bash', hook,
             os.path.join(SAMPLES, 'clover-official-sample.plist')],
            cwd=CC, capture_output=True, text=True,
            env=dict(os.environ, CHECKER_BUILD='1'))
expect(p.returncode == 0 and 'documentation suffix' not in p.stdout
       and 'Summary: 0 errors, 0 warnings, 0 notes' in p.stdout,
       'wrapper + CHECKER_BUILD=1 -> clean build report',
       p.stdout + p.stderr)

# 32c. wrapper with NO argument, sample auto-resolved from the tree
#      -> build mode (clean 0/0/0): the end-of-build behaviour
fake_v2b = os.path.join(TMP, 'fake_clover_pkg_official')
os.makedirs(os.path.join(fake_v2b, 'EFI', 'CLOVER'), exist_ok=True)
shutil.copy(os.path.join(SAMPLES, 'clover-official-sample.plist'),
            os.path.join(fake_v2b, 'EFI', 'CLOVER', 'config-sample.plist'))
p = sp2.run(['bash', hook],
            cwd=CC, capture_output=True, text=True,
            env=dict(os.environ, CLOVER_PKG_DIR=fake_v2b, CLOVER_CONFIG=''))
expect(p.returncode == 0 and 'documentation suffix' not in p.stdout
       and 'Summary: 0 errors, 0 warnings, 0 notes' in p.stdout
       and 'config.plist is valid' in p.stdout,
       'wrapper no-arg auto-detect -> build mode on the tree sample',
       p.stdout + p.stderr)

# 33. --oneline with problems: header + indented issue lines, no checklist
rc, out = run('--oneline', os.path.join(TMP, 'no_quirks.plist'))
expect(rc == 1 and 'INVALID' in out and '  ERROR:' in out
       and 'Verified sections:' not in out and 'Summary:' not in out,
       '--oneline: problems indented under the header, no checklist', out)

# 34. CHECKER_QUIET=1 opts into the compact one-line output
p = sp2.run(['bash', hook, os.path.join(SAMPLES, 'config-valid.plist')],
            cwd=CC, capture_output=True, text=True,
            env=dict(os.environ, CHECKER_QUIET='1'))
expect(p.returncode == 0 and '-- VALID' in p.stdout
       and 'Verified sections:' not in p.stdout
       and 'config.plist is valid' not in p.stdout,
       'CHECKER_QUIET=1 -> compact one-line output',
       p.stdout + p.stderr)

# 35. CHECKER_QUIET=1 output is EXACTLY one line
p = sp2.run(['bash', hook, os.path.join(SAMPLES, 'config-valid.plist')],
            cwd=CC, capture_output=True, text=True,
            env=dict(os.environ, CHECKER_QUIET='1'))
lines = [l for l in p.stdout.splitlines() if l.strip()]
expect(p.returncode == 0 and len(lines) == 1 and '-- VALID' in lines[0],
       'CHECKER_QUIET=1 output is exactly one line', p.stdout)

# 36. build mode renders '?'-sections under their clean base name --
#     one uniform checklist (no inert tag, no '?' in section rows)
rc, out = run('--build', os.path.join(SAMPLES, 'clover-official-sample.plist'))
expect(rc == 0 and 'DisableDrivers:' in out
       and 'DisableDrivers?:' not in out and 'inert' not in out
       and '2 keys verified' in out,
       'build mode: DisableDrivers? shown uniformly as DisableDrivers', out)

# 37. manual mode keeps the educational inert tag (no regression)
rc, out = run(os.path.join(SAMPLES, 'clover-official-sample.plist'))
expect(rc == 0 and 'DisableDrivers?:' in out
       and 'inert (Clover ignores "?" keys)' in out,
       'manual mode: ?-section keeps the inert explanation', out)

print()
print('FAILED:' if fails else 'ALL TESTS PASSED', fails if fails else '')
sys.exit(1 if fails else 0)
