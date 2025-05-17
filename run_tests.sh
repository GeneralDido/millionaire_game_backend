#!/bin/bash
set -e

# Load test environment variables if .env.test exists
if [ -f .env.test ]; then
    # shellcheck disable=SC2046
    export $(grep -v '^#' .env.test | xargs)
fi

# Install test dependencies if needed
pip install -r requirements-dev.txt

# Run the tests
python -m pytest -xvs tests/