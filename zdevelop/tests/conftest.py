import pytest
import sys


min_version = pytest.mark.skipif(
    sys.version_info[:2] < (3, 7), reason="Test requires Python 3.7 or Higher"
)
