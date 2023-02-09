#!/bin/bash

set -x

PATH="${PATH}:/c/msys32/mingw32/bin"
source "$(pwd)/.gitlab/env/windows.env"

cd tryton || exit 1
git fetch --tags --all -p -f
git reset --hard origin/master
git clean -fd
git checkout "${CI_COMMIT_REF_NAME:?}"
"$(pwd)/win-make.sh" build "${COOPENGO_SOFTWARE_CERT_PASSWORD:?}"
