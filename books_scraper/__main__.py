"""Allow ``python -m books_scraper``."""

import sys

from .cli import main

sys.exit(main())
