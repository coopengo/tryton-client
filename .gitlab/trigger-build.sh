#!/bin/bash

set -x

PATH="${PATH}:/c/msys32/mingw32/bin"

source .gitlab/env/windows.env
git fetch --tags --all -p -f
git reset --hard origin/master
git clean -fd
git checkout "${CI_COMMIT_REF_NAME:?}"
git pull --all --tags -f -p
win-make.sh build "${COOPENGO_SOFTWARE_CERT_PASSWORD:?}"
