#!/bin/bash

# Exit with nonzero exit code if anything fails
set -eo pipefail
# Ensure the script is running in this directory
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

LANGUAGES=("de_DE" "fr_FR" "es_ES")
NEW_TRANSLATION_FILES=()
NEW_TRANSLATION_REGEX='\([1-9][0-9]* new and [0-9]* already existing\)'

echo "Collecting translations from
    - src/*.py
    - uis/mainwindow.ui"
echo "Targetting languages:"
for LANGUAGE in "${LANGUAGES[@]}"; do
    echo "    - $LANGUAGE"
done

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -n | --no-obsolete)
      NO_OBSOLETE=true
      shift
      ;;
  esac
done

OPTIONS=()
if [[ -n $NO_OBSOLETE ]]; then
    OPTIONS+=("-no-obsolete")
fi


for LANGUAGE in "${LANGUAGES[@]}"; do
    OUTPUT=$(poetry run pyside6-lupdate ../uis/mainwindow.ui -ts "../translations/mainwindow_$LANGUAGE.ts" "${OPTIONS[@]}")
    echo "$OUTPUT"
    if [[ $OUTPUT =~ $NEW_TRANSLATION_REGEX ]]; then
        NEW_TRANSLATION_FILES+=("mainwindow_$LANGUAGE.ts")
    fi
    OUTPUT=$(poetry run pyside6-lupdate ../src/*.py -ts "../translations/main_$LANGUAGE.ts" "${OPTIONS[@]}")
    echo "$OUTPUT"
    if [[ $OUTPUT =~ $NEW_TRANSLATION_REGEX ]]; then
        NEW_TRANSLATION_FILES+=("main_$LANGUAGE.ts")
    fi
done

if [[ ${#NEW_TRANSLATION_FILES[@]} -eq 0 ]]; then
    echo "No new translations found"
else
    echo "New translations found for:"
    for FILE in "${NEW_TRANSLATION_FILES[@]}"; do
        echo "    - $FILE"
    done
fi