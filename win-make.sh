#!/bin/bash

set -x

GDRIVE_FOLDER_ID=1wrsfp7PBa8Sdg7nh4lJnx2FmYAtdGATq
CERTIFICAT_PASSWORD=$2
WINDOWS_USER_PASSWORD=$3

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
        mingw-w64-i686-python3 \
        mingw-w64-i686-python3-setuptools \
        mingw-w64-i686-python3-pip \
        mingw-w64-i686-gtk3 \
        mingw-w64-i686-python3-gobject \
        mingw-w64-i686-gtksourceview3 \
        mingw-w64-i686-gtkglext \
        mingw-w64-i686-python3-cx_Freeze \
        mingw-w64-i686-gobject-introspection \
        mingw-w64-i686-goocanvas \
        mingw-w64-i686-gtksourceview3 \
        mingw-w64-i686-evince


    pip install \
        python-dateutil \
        chardet \
        pyflakes

    echo "gdrive should be installed from https://github.com/glotlabs/gdrive#downloads"
    echo "gdrive should be placed in a PATH folder"
}

clean() {
    rm -rf build dist coog-*
}

build() {
    clean
    local v; v=$(version)
    python setup-freeze.py install_exe -d dist
    "C:/PSTools/PsExec.exe" -u Administrator -p ${WINDOWS_USER_PASSWORD} "C:\msys32\home\Administrator\tryton\sign-client.bat" ${CERTIFICAT_PASSWORD}
    makensis -DVERSION="$v" -DBITS=32 -DSERIES="$v" setup.nsi
    # makensis -DVERSION="$v" -DBITS=32 setup-single.nsi
    mv dist "$v"
    "C:/PSTools/PsExec.exe" -u Administrator -p ${WINDOWS_USER_PASSWORD} "C:\msys32\home\Administrator\tryton\sign-client.bat" ${CERTIFICAT_PASSWORD}
    zip -q -9 -r "coog-$v.zip" "$v"
}

upload() {
    for f in ./coog-*
    do
        gdrive files upload --parent "$GDRIVE_FOLDER_ID" "$f"
    done
}

main() {
    [ -z "$1" ] && echo missing command && return 1
    "$1" "$@"
}

main "$@"
