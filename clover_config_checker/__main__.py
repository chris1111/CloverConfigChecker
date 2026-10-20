"""Allow `python -m clover_config_checker <config.plist>`."""
import sys

from .cli import main

sys.exit(main())
