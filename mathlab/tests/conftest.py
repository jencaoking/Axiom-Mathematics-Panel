import os
import pytest

# For headless testing in CI without X11/OpenGL issues
os.environ["QT_QPA_PLATFORM"] = "offscreen"
