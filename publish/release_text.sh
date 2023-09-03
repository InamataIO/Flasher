#!/bin/bash

LAST_TAG=$(git describe HEAD~ --abbrev=0 --tags)
# shellcheck disable=SC2005
echo "$(git log --pretty=format:'### %s%n%n%b' "$LAST_TAG"..HEAD)"
