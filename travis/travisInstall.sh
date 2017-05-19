#!/bin/bash
set -e -x

python --version
pip --version

python -c "import sys; sys.exit(sys.version_info[:2] != (3,2))" 2>/dev/null || pip install -U pip wheel
pip install cibuildwheel==0.2.0
pip install -r requirements.txt
pip install -U beautifulsoup4 cssselect
pip install cibuildwheel==0.2.0