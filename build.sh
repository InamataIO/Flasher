#!/bin/bash

# https://stackoverflow.com/questions/428109/extract-substring-in-bash
tmp=$(grep '^version = ".*"$' pyproject.toml)
tmp=${tmp#*\"}
PYPROJECT_VERSION=${tmp%\"*}

tmp=$(grep '^__version__ = ".*"$' src/main.py)
tmp=${tmp#*\"}
MAINPY_VERSION=${tmp%\"*}

tmp=$(grep '^version: .*$' snap/snapcraft.yaml)
SNAPCRAFT_VERSION=${tmp:9}

if [ "$PYPROJECT_VERSION" = "$MAINPY_VERSION" ] && [ "$MAINPY_VERSION" = "$SNAPCRAFT_VERSION" ]; then
  echo "Building $MAINPY_VERSION for PyInstaller and Snapcraft"
else
  echo -e "Not all versions equal\npyproject.toml: $PYPROJECT_VERSION\nsrc/main.py: $MAINPY_VERSION\nsnap/snapcraft.yaml: $SNAPCRAFT_VERSION"
fi

GIT_TAG=$(git describe --tags HEAD)
GIT_VERSION="${GIT_TAG:1}"
if [[ -n $(git status -s) ]]; then
  GIT_VERSION="$GIT_VERSION-dirty"
  echo "Git repo is dirty"
fi
PYINSTALLER_TARGET_NAME="inamata_flasher-$GIT_VERSION-linux-x86_64"

echo "Building the Linux PyInstaller package"
poetry run pyinstaller main.spec
cp dist/inamata_flasher "dist/$PYINSTALLER_TARGET_NAME"
echo "dist/$PYINSTALLER_TARGET_NAME"

echo "Building the Snapcraft package"
snapcraft