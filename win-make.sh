#!/bin/bash

version() {
  local t
  t=$(git describe --tags --exact-match 2> /dev/null | grep "^coog-" | head -1)
  if [ ! -z "$t" ]
  then
    echo "${t//coog-/}"
  else
    local b; b=$(git rev-parse --abbrev-ref HEAD)
    local c; c=$(git rev-parse --short HEAD)
    echo "$b-$c" | sed -e "s/coog-//g"
  fi
}

deps() {
  pacman -S \
    mingw-w64-i686-librsvg \
    mingw-w64-i686-nsis \
    mingw-w64-i686-python2 \
    mingw-w64-i686-python2-setuptools \
    mingw-w64-i686-python2-pip \
    mingw-w64-i686-python2-pygtk \
    mingw-w64-i686-gtk-engine-murrine \
    mingw-w64-i686-python2-cx_Freeze

  pip install \
    python-dateutil \
    chardet \
    pyflakes
}

clean() {
  rm -rf build dist coog-*
}

patch() {
  git apply win-patch.diff
}

unpatch() {
  git checkout HEAD -- tryton
}

build() {
  clean
  patch
  local v; v=$(version)
  python setup-freeze.py install_exe -d dist
  makensis -DVERSION="$v" setup.nsi
  makensis -DVERSION="$v" setup-single.nsi
  unpatch
}

main() {
  [ -z "$1" ] && echo missing command && return 1
  "$1" "$@"
}

main "$@"
