#!/bin/bash

LAST_TAG=$(git describe HEAD~ --abbrev=0 --tags)
git log --pretty=format:'### %s%n%n%b' "$LAST_TAG"..HEAD
