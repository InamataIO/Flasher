#!/bin/bash

# Exit with nonzero exit code if anything fails
set -eo pipefail
# Ensure the script is running in this directory
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

LANGUAGES=("de_DE" "fr_FR" "es_ES")

for LANGUAGE in "${LANGUAGES[@]}"; do
    poetry run pyside6-lupdate ../uis/mainwindow.ui -ts "../translations/mainwindow_$LANGUAGE.ts"
    poetry run pyside6-lupdate ../src/*.py -ts "../translations/main_$LANGUAGE.ts"
done
