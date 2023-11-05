#!/bin/bash

# Exit with nonzero exit code if anything fails
set -eo pipefail
# Ensure the script is running in this directory
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

PYINSTALLER_PARAMS=("--distpath" "../dist" "--workpath" "../build" "-y")

parse_info_file_version() {
  tmp=${tmp#*(}
  tmp=${tmp%)*}
  IFS=', ' read -ra ADDR <<< "$tmp"
  INFO_VERSION=${ADDR[0]}
  for i in "${!ADDR[@]}"; do
    # Only set 2nd and 3rd number (0, 4, 11, 0)
    if (( i == 1 )) || (( i == 2 )); then
      INFO_VERSION="$INFO_VERSION.${ADDR[$i]}"
    fi
  done
  echo "$INFO_VERSION"
}

package_linux() {
  echo "Building $GIT_VERSION for PyInstaller and Snapcraft"
  poetry run pyinstaller "${PYINSTALLER_PARAMS[@]}" ../publish/one-file.spec

  # Copy PyInstaller binary with release name
  PYINSTALLER_TARGET_NAME="inamata_flasher-$GIT_VERSION-linux-x86_64"
  cp ../dist/inamata_flasher "../dist/$PYINSTALLER_TARGET_NAME"
  echo "../dist/$PYINSTALLER_TARGET_NAME"

  echo "Building the Snapcraft package"
  CWD=$PWD
  cd ..
  snapcraft
  cd "$CWD"
}

package_windows() {
  echo "Building $GIT_VERSION for PyInstaller and Inno Setup"
  poetry run pyinstaller "${PYINSTALLER_PARAMS[@]}" ../publish/one-file.spec

  # Copy PyInstaller binary with release name
  PYINSTALLER_TARGET_NAME="inamata_flasher-$GIT_VERSION-windows-x86_64"
  cp ../dist/inamata_flasher "../dist/$PYINSTALLER_TARGET_NAME"
  echo "../dist/$PYINSTALLER_TARGET_NAME"

  echo "Building the Inno Setup package"
  poetry run pyinstaller "${PYINSTALLER_PARAMS[@]}" ../publish/one-dir.spec
  
  if [[ -z $ISCC_PATH ]]; then
    ISCC_PATH='/c/Program Files (x86)/Inno Setup 6/ISCC.exe'
  fi
  ABSOLUTE_ISS_PATH="$(realpath ../publish/main.iss)"
  WINDOWS_ISS_PATH="$(cygpath -w "$ABSOLUTE_ISS_PATH")"
  "$ISCC_PATH" "$WINDOWS_ISS_PATH"
}

PYPROJECT_FILE="../pyproject.toml"
MAINPY_FILE="../src/main.py"
SNAPCRAFT_FILE="../snap/snapcraft.yaml"
INNO_FILE="../publish/main.iss"
INFO_FILE="../publish/windows/file_version_info.txt"

./compile_translations.sh

# https://stackoverflow.com/questions/428109/extract-substring-in-bash
tmp=$(grep '^version = ".*"$' "$PYPROJECT_FILE") || true
tmp=${tmp#*\"}
PYPROJECT_VERSION=${tmp%\"*}
VERSIONS=("$PYPROJECT_VERSION")

tmp=$(grep '^__version__ = ".*"$' "$MAINPY_FILE") || true
tmp=${tmp#*\"}
MAINPY_VERSION=${tmp%\"*}
VERSIONS+=("$MAINPY_VERSION")

tmp=$(grep '^version: .*$' "$SNAPCRAFT_FILE") || true
SNAPCRAFT_VERSION=${tmp:9}
VERSIONS+=("$SNAPCRAFT_VERSION")

tmp=$(grep '^#define MyAppVersion .*$' $INNO_FILE) || true
tmp=${tmp#*\"}
INNO_VERSION=${tmp%\"*}
VERSIONS+=("$INNO_VERSION")

tmp=$(grep 'filevers=(.*),$' "$INFO_FILE") || true
INFO_FILE_TPL_VERSION=$(parse_info_file_version "$tmp")
VERSIONS+=("$INFO_FILE_TPL_VERSION")

tmp=$(grep 'prodvers=(.*),$' "$INFO_FILE") || true
INFO_PROD_TPL_VERSION=$(parse_info_file_version "$tmp")
VERSIONS+=("$INFO_PROD_TPL_VERSION")

tmp=$(grep "StringStruct('FileVersion', '.*\.windows'),$" "$INFO_FILE") || true
tmp=${tmp:37}
INFO_FILE_STR_VERSION=${tmp%\.windows*}
VERSIONS+=("$INFO_FILE_STR_VERSION")

tmp=$(grep "StringStruct('ProductVersion', '.*\.windows'),$" "$INFO_FILE") || true
tmp=${tmp:40}
INFO_PROD_STR_VERSION=${tmp%\.windows*}
VERSIONS+=("$INFO_PROD_STR_VERSION")

for i in "${VERSIONS[@]}"; do
    if [[ ${VERSIONS[0]} != "$i" ]]; then
      VERSIONS_UNEQUAL=True
    fi
done

if [[ -z $VERSIONS_UNEQUAL ]]; then
  echo "All ${#VERSIONS[@]} version numbers are the same"
else
  echo "Not all versions equal
$PYPROJECT_FILE: $PYPROJECT_VERSION
$MAINPY_FILE: $MAINPY_VERSION
$SNAPCRAFT_FILE: $SNAPCRAFT_VERSION
$INNO_FILE: $INNO_VERSION
$INFO_FILE (filevers): $INFO_FILE_TPL_VERSION
$INFO_FILE (prodvers): $INFO_PROD_TPL_VERSION
$INFO_FILE (FileVersion): $INFO_FILE_STR_VERSION
$INFO_FILE (ProductVersion): $INFO_PROD_STR_VERSION"
  exit 1
fi

# If not on tagged commit adds offset (v0.4.11-1-gd0e2f86)
GIT_TAG=$(git describe --tags HEAD)
GIT_VERSION="${GIT_TAG:1}"
if [[ -n $(git status -s) ]]; then
  GIT_VERSION="$GIT_VERSION-dirty"
  echo "Git repo is dirty"
fi

# If Git version equals the Git clean tag, assue we're building release.
# In that case ensure that the Git tag matches the other version numbers.
# If they do not equal, GIT_VERSION is clearly marked as dirty which should
# avoid incorrect binaries being accidentally published.
# If not on tagged commit only returns tag
GIT_CLEAN_TAG=$(git describe --abbrev=0 --tags)
if [[ "$GIT_VERSION" == "$GIT_CLEAN_TAG" ]]; then
  GIT_CLEAN_VERSION="${GIT_CLEAN_TAG:1}"
  if [[ ${VERSIONS[0]} != "$GIT_CLEAN_VERSION" ]]; then
    echo "Git tag $GIT_CLEAN_VERSION does not match other versions ${VERSIONS[0]}"
    exit 1
  fi
fi

if [[ -z $UNAME_OUT ]]; then
  UNAME_OUT=$(uname -s)
fi
case "$UNAME_OUT" in
    Linux*)     BUILD_OS=Linux;;
    Darwin*)    BUILD_OS=Mac;;
    CYGWIN*)    BUILD_OS=Windows;;
    MINGW*)     BUILD_OS=Windows;;
    MSYS_NT*)   BUILD_OS=Windows;;
    *)
esac
if [[ $BUILD_OS == "Linux" ]]; then
  echo "Packaging for Linux"
  package_linux
elif [[ $BUILD_OS == "Windows" ]]; then
  echo "Packaging for Windows"
  package_windows
else
  echo "Unsupported OS: $UNAME_OUT"
  exit 1
fi
