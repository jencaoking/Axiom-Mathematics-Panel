import os
import sys
import pytest

# Headless Qt testing (no X11/OpenGL needed)
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# NOTE: Do NOT add project root to sys.path here.
# Individual test files handle their own imports to avoid
# triggering mathlab/__init__.py's full Qt import chain.
