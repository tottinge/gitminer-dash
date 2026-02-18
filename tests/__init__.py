"""
Test package for gitminer-dash.

This package contains all the tests for the gitminer-dash project.
"""

import os
import sys

# Add the parent directory to the path so we can import modules from the root
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)


def setup_path():
    """
    Add the parent directory to the Python path.

    This function is called by test modules to ensure they can import
    modules from the project root directory.
    """
    # This function exists to document the path setup that happens on import
    pass
