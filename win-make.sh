#!/bin/bash

# For build
CERTIFICAT_PASSWORD=$2
WINDOWS_USER_PASSWORD=$3

# For upload
GITHUB_TOKEN=$2

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
        mingw-w64-i686-gtksourceview3


    pip3.6 install \
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
    python3.6 setup-freeze.py install_exe -d dist
    makensis -DVERSION="$v" -DSERIES="$v" setup.nsi
    makensis -DVERSION="$v" setup-single.nsi
}

upload() {
    local v; v=$(version)

    CREATE_RELEASE=$(curl -L -X POST -H "Accept: application/vnd.github+json" -H "Authorization: Bearer ${GITHUB_TOKEN}" -H "X-GitHub-Api-Version: 2022-11-28" https://api.github.com/repos/coopengo/tryton/releases -d "{\"tag_name\":\"coog-$v\",\"name\":\"coog-$v\",\"body\":\"Coog client for coog-$v\",\"make_latest\":\"false\"}")
    UPLOAD_URL=$(echo "${CREATE_RELEASE}" | jq -r '.upload_url' | sed 's/{?name,label}//')

    for f in ./coog-*
    do
        curl -X POST -H "Content-Type: application/octet-stream" --data-binary "@${f/.\/}" -H "Authorization: Bearer ${GITHUB_TOKEN}" "${UPLOAD_URL}?name=${f/.\/}"
    done
}

main() {
    [ -z "$1" ] && echo missing command && return 1
    "$1" "$@"
}

main "$@"
