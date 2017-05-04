#!/bin/bash
set -x -e


if [ -z "${DOCKER_IMAGE}" ]; then

    if [[ "${TRAVIS_OS_NAME}" == "osx" ]]; then
        eval "$(/usr/local/bin/pyenv init -)"
        pyenv global "${PYENV_VERSION}"
    fi

    iconv --version
    python --version
    pip --version
    python -u setup.py clean

    if [[ "${TRAVIS_OS_NAME}" == "osx" ]]; then
        make wheel_static
    fi
else
   make wheel_manylinux
fi
