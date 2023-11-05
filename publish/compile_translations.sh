#!/bin/bash

# Exit with nonzero exit code if anything fails
set -eo pipefail
# Ensure the script is running in this directory
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

for i in ../translations/*.ts; do
    [ -f "$i" ] || break
    poetry run pyside6-lrelease "$i" -qm "${i%.*}.qm"
done
