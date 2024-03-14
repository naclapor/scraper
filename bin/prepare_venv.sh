#!/bin/bash

SCRIPTPATH="$(dirname $0)"

pushd "$SCRIPTPATH/.." > /dev/null

if [ -d ./venv ]; then
    echo "venv folder exists. Delete it to rebuild the virtual env"
    exit 0
fi

python3 -m virtualenv ./venv
source ./venv/bin/activate

pushd /tmp
git clone https://github.com/mitmproxy/mitmproxy.git
cd mitmproxy
pip install .
popd

popd  > /dev/null
