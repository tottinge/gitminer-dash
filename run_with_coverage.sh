#!/bin/bash

# Clear any existing coverage data
rm -f .coverage

# Run the app with coverage
echo "Starting app with coverage tracking..."
echo "Press Ctrl+C when done testing"
echo "NOTE: Running with debug=False to enable proper coverage tracking"
echo "(Auto-reload is disabled so you must restart if you change code)"
echo ""

# Set env var to disable reloader for coverage
export COVERAGE_RUN=true
uv run coverage run --source=. app.py "$@"

# Generate coverage report
echo ""
echo "Generating coverage report..."
uv run coverage report --show-missing

# Generate detailed HTML report
uv run coverage html
echo ""
echo "HTML coverage report generated in htmlcov/index.html"
