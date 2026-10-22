CloverConfigChecker -- check any Clover config.plist
Pure Python -- no install needed -- macOS, Linux, Windows


WHAT IT IS
----------
A small tool that reads a Clover EFI config.plist and tells you,
in plain text, whether the file is sound -- BEFORE you install
it or reboot with it.

It works on ANY Clover config.plist, wherever the file is:

  - a config.plist sitting on your Desktop
  - the config on your EFI partition right now
  - a config you downloaded, or got from a forum or a friend
  - a config you are editing by hand
  - a fresh config.plist from a new Clover install
  - a config on a USB installer stick

It only reads the file. It never changes anything.


WHY USE IT
----------
- A typo in config.plist can keep a system from booting. The
  checker finds typos, wrong values and missing sections in
  seconds -- no reboot cycles needed.

- Typos come with suggestions:

    ERROR: unknown key (similar to 'Timeout') at Boot/TimeOut

- Values are really checked, not just key names: booleans,
  numbers and hex values, UUID format, allowed choices,
  sensible ranges.

- It explains Clover's own conventions: keys ending in "?"
  are IGNORED by Clover, so a setting stored that way may
  silently not apply. The report points them out.

- Missing required parts are caught. On modern Clover an
  empty or missing Quirks section is a hard error.

- No installation, no extras: pure Python 3.8+.


HOW TO USE IT -- WHAT TO TYPE
-----------------------------
The tool lives in its own folder: CloverConfigChecker/.

You give it ONE thing: the path to the config.plist you want
checked. The config file can be anywhere.

Open a terminal, go into the folder, then type the command
followed by the path to your config:

  cd /path/to/CloverConfigChecker

Example 1 -- a config.plist sitting on your Desktop:

  macOS / Linux:

    ./run_config_check.sh ~/Desktop/config.plist

  Windows (Command Prompt):

    python -m clover_config_checker %USERPROFILE%\Desktop\config.plist

Example 2 -- the config on your EFI partition:

  macOS:

    ./run_config_check.sh /Volumes/EFI/EFI/CLOVER/config.plist

  Linux:

    ./run_config_check.sh /mnt/usb/EFI/CLOVER/config.plist

  Windows:

    python -m clover_config_checker D:\EFI\CLOVER\config.plist

Example 3 -- run it from ANY directory, without cd first:
give the FULL path of the script, then the config path:

  /path/to/CloverConfigChecker/run_config_check.sh ~/Desktop/config.plist

Every run prints a section-by-section report ending in a
verdict: VALID or INVALID. That is all there is to it.

Checking several files at once:

  python3 -m clover_config_checker ~/Desktop/config.plist \
      /Volumes/EFI/EFI/CLOVER/config.plist

Optional -- prefer a permanent command? From inside the folder,
install it once:

     pipx install .          (or: pip install .)

after that, from any directory:

     clover-config-checker ~/Desktop/config.plist


### NEW: Use from Github Pages ➥ [Clover Config Checker](https://chris1111.github.io/CloverConfigChecker/)

READING THE REPORT
------------------
A clean run looks like this:


    CloverConfigChecker -- validating config.plist
  --------------------------------------------------------------
    config : /Users/chris/Desktop/config.plist


  Verified sections:
    ACPI:                 20 keys verified
    Boot:                  7 keys verified
    Quirks:               19 keys verified
    Total:                120 keys in 11 sections

  Summary: 0 errors, 0 warnings, 0 notes
  Result: VALID

- "Verified sections" is the list of what was actually
  checked, one line per section.

- Problem lines appear ABOVE that list. Three levels:

    ERROR:   broken -- unknown key, wrong type, bad hex or
             UUID. Fix these; they are real mistakes.
    WARNING: suspicious -- out-of-range value, deprecated
             key, duplicate key. Usually worth fixing.
    NOTE:    information only -- e.g. keys ending in "?"
             are documentation keys that Clover ignores.

- "Result: INVALID" always comes with the exact lines to fix.


QUESTIONS PEOPLE ASK
--------------------

Q: Can it break my system or my config?
A: No. The checker only reads the file. It never writes,
   moves or deletes anything.

Q: config-sample.plist from Clover source code shows ~128 NOTE lines about "?" keys.
   Is something wrong?
A: No. Clover's official sample config uses keys ending in
   "?" as built-in documentation; Clover ignores them. The
   report simply tells you those settings are not active.
A: It is strongly suggested that you review the source `config.plist` and adapt it to your own configuration.

Q: It says INVALID. What now?
A: Fix the ERROR lines one by one -- each names the section,
   the key and the problem, often with a suggestion in
   brackets. Re-run until you get Result: VALID.

Q: I am saving the output to a file and don't want colors.
A: Use --color never (or set NO_COLOR=1). The text itself is
   always plain and searchable.


ALL OPTIONS
-----------
  python3 -m clover_config_checker [options] config.plist ...

    --brief       minimal output, no section list
    --quiet, -q   only the Result line per file
    --oneline     one line per file (log style)
    --strict, -s  warnings also fail (useful in scripts)
    --color W     auto (default), always, never
    --version     show version

Exit codes, for scripts and automation:
    0 = valid      1 = invalid      2 = file unreadable


FOR DEVELOPERS
--------------
- Schema (add new Clover keys here): clover_config_checker/schema_clover.py
- Run the test suite:               python3 test_cli.py
- License: MIT, see LICENSE

----------------------------------------------------------------
CloverConfigChecker v1.8.3 -- MIT license.
A companion tool for the Clover EFI bootloader.

 
  
