#!/bin/bash

SCRIPTPATH="$(dirname $0)"
pushd "$SCRIPTPATH/.." > /dev/null

if [ $# -eq 0 ]; then
    echo "usage: $0 <target_name>"
    exit 1
fi

if [ ! -d ./venv ]; then
    echo "missing virtualenv, create it first"
    exit 1
fi
source ./venv/bin/activate

target="$1"
export SCRAPER_TARGET_NAME="$target"
mitmdump --set connection_strategy=lazy -s ./replayer.py

popd > /dev/null
