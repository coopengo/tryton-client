#!/bin/bash

set -x

PATH="${PATH}:/c/msys32/mingw32/bin"

cd tryton
pwd
/usr/bin/git fetch --tags --all -p -f
/usr/bin/git reset --hard origin/master
/usr/bin/git clean -fd
/usr/bin/git checkout "${CI_COMMIT_REF_NAME:?}"
source $(pwd)/.gitlab/env/windows.env
$(pwd)/win-make.sh build "${COOPENGO_SOFTWARE_CERT_PASSWORD:?}"