#!/bin/bash

if [[ $TRAVIS_OS_NAME == 'osx' ]]; then
    source venv/bin/activate
fi

python -u setup.py clean
CFLAGS="-O0 -g" python -u setup.py build_ext --inplace
CFLAGS="-O0 -g" PYTHONUNBUFFERED=x make test
python setup.py bdist_wheel