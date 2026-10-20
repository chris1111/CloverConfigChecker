"""ANSI colour helpers for CloverConfigChecker (pure stdlib).

Colours help users see at a glance what was verified:
ERROR = red, WARNING = yellow, NOTE = cyan, VALID = green.

Colour is enabled automatically when the output stream is a terminal
and disabled when output is piped (into grep, log files, CI logs), so
machine-readable output is never polluted with escape codes.

Override behaviour with:
  --color always|never|auto   (CLI flag, default: auto)
  NO_COLOR=1                  (https://no-color.org -- disables in auto mode)
  FORCE_COLOR=1               (forces colour in auto mode, e.g. in CI)
"""

import os
import sys

# ANSI SGR escape codes
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'
RED = '\033[31m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
CYAN = '\033[36m'


def _windows_enable_vt() -> bool:
    """Enable ANSI escape processing on Windows 10+ consoles."""
    if os.name != 'nt':
        return True
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)          # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))
    except Exception:
        return False


def use_color(stream=None, mode: str = 'auto') -> bool:
    """Decide whether to paint output. mode: auto | always | never."""
    if mode == 'never':
        return False
    if mode == 'always':
        return True
    # auto
    if os.environ.get('NO_COLOR'):
        return False
    if os.environ.get('FORCE_COLOR'):
        return True
    stream = stream if stream is not None else sys.stdout
    if not hasattr(stream, 'isatty') or not stream.isatty():
        return False
    if os.environ.get('TERM') == 'dumb':
        return False
    return _windows_enable_vt()


def paint(text: str, *codes: str, enabled: bool = True) -> str:
    """Wrap `text` in the given ANSI codes (no-op when disabled)."""
    if not enabled or not codes:
        return text
    return ''.join(codes) + text + RESET
