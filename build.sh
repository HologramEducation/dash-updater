#!/bin/bash

set -e

OS="`uname`"
PLATFORM='unknown'
VE="ve/bin/"
MAKEZIP=0
PIFLAGS=''
case $OS in
  'Linux')
      PLATFORM="$(uname -m)-pc-linux-gnu"
    ;;
  MINGW32*)
      PLATFORM="i686-mingw32"
      VE="ve/Scripts/"
      MAKEZIP=1
      PIFLAGS="--icon icons/hologram.ico"
      export TCL_LIBRARY=/c/Python27/tcl/tcl8.5
    ;;
  'Darwin')
      PLATFORM="x86_64-apple-darwin"
      PIFLAGS="--icon icons/hologram.icns"
    ;;
  *)
    echo 'Invalid OS'
    exit
esac

version=$(cat version.txt)
buildname="dashupdater-$version-$PLATFORM"

if [ VE -a ! -d ./ve ] ; then
    virtualenv ve
fi

PIP=$VE
PIP+=pip
$PIP install --upgrade pip
$PIP install -r requirements.txt

PM=$VE
PM+=pyi-makespec
$PM $PIFLAGS -F -n dashupdater dashupdater.py

#This .bak and then deletion is to maintain compatibility with BSD sed
sed -i.bak "s/datas=\[\]/datas=\[\('version.txt', '.'\)\]/" dashupdater.spec
rm dashupdater.spec.bak

PI=$VE
PI+=pyinstaller
$PI dashupdater.spec

cd dist
mkdir -p $buildname/bin/
cp dashupdater $buildname/bin/
tar -jcvf $buildname.tar.bz2 $buildname

if [ "$MAKEZIP" -eq "1" ] ; then
    zip -r $buildname.zip $buildname
fi
