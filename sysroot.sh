#!/usr/bin/env bash
set -e

TMP=$(mktemp -d)
SYSROOT=${1:-"sysroot"}

wget -c -P $TMP -i packages.txt

find $TMP -name '*.deb' | xargs -I@ dpkg -x @ $SYSROOT

ln -s "$SYSROOT/data/data/com.termux/files/*" "$SYSROOT/"

echo "INPUT(-lc)" > "$SYSROOT/usr/lib/libpthread.so"

rm -r $TMP
