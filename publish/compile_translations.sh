#!/bin/bash

# Exit with nonzero exit code if anything fails
set -eo pipefail
# Ensure the script is running in this directory
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

UNTRANSLATED_FILES=()
UNTRANSLATED_REGEX='untranslated source text'

for FILE in ../translations/*.ts; do
    [ -f "$FILE" ] || break
    OUTPUT=$(poetry run pyside6-lrelease "$FILE" -qm "${FILE%.*}.qm")
    echo "$OUTPUT"
    if [[ $OUTPUT =~ $UNTRANSLATED_REGEX ]]; then
        UNTRANSLATED_FILES+=("$FILE")
    fi
done

if [[ ${#UNTRANSLATED_FILES[@]} -ne 0 ]]; then
    echo "WARNING: Untranslated text found in:"
    for FILE in "${UNTRANSLATED_FILES[@]}"; do
        echo "    - ${FILE##*/}"
    done
fi