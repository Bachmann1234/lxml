#!/bin/bash

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
    brew update
    brew install python3
    python3 -m venv venv
    source venv/bin/activate
fi
python -c "import sys; sys.exit(sys.version_info[:2] != (3,2))" 2>/dev/null || pip install -U pip wheel
pip install --install-option="--no-cython-compile" -r requirements.txt
pip install -U beautifulsoup4 cssselect