# Development Guide

[[TOC]]

## Start

1. Do the [driver setup](#driver-setup-instructions)
2. In a terminal run `poetry install`
3. Run `./start.sh` or `poetry run python src/main.py`

## Release Process

Push the final version (with updated version numbers), create a new release on Github, create a distributable binary for each platform and upload the releases to the Github release.

### Bump Version Numbers

When building the release artefacts, pass `-P bump=<major/minor/patch>` to the build command. For example to increment the minor version run:

```sh
./build.sh -P bump=minor
```

If bump is not passed, a development release is generated. The `version.h` and `version.rc` files are currently not used. They were used to sign binaries but now `file_version_info.txt` is used.

### Release Text

To generate a summary of the build, run the following command:

```sh
./build.sh text
```

### Windows

After [obtaining](https://comodosslstore.com/codesigning.aspx) a code signing certificate and installing the [Windows sign tool](https://stackoverflow.com/a/65339931), run the following commands:

    poetry install
    poetry shell
    pyinstaller main.spec

Open a command prompt terminal to sign the executables

    cd C:\Program Files (x86)\Windows Kits\10\bin\x64\
    signtool.exe sign /sha1 "dfeb0472436c54494de4f3641d2a1d17acc8ead2" /tr http://time.certum.pl/ /td sha256 /fd sha256 /v <path-to-exe>

    OR

    "c:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe" sign /sha1 "dfeb0472436c54494de4f3641d2a1d17acc8ead2" /tr http://time.certum.pl/ /td sha256 /fd sha256 /v <path-to-exe>

For instructions to set up the code signing, check the [setup instructions](https://www.files.certum.eu/documents/manual_en/Signing_with_the_use_of_jarsigner_tool_and_signtool.pdf).

### Linux

The `build.sh` script will build a standalone PyInstaller as well as a Snap package. Attach the PyInstaller image to the GitHub release. For the Snap package, promote it on snapcraft.io to the release channel. After pushing to the candidate channel, start the Ubuntu 22.04, 20.04 and Kubuntu 22.04 VMs and start the app. Then logout and switch to the X or Wayland session. This should cover most distro dependent differences.

To manually create a PyInstaller distributable, run the following commands:

    poetry install
    poetry shell
    pyinstaller main.spec

The standalone executeable can be found in `dist/inamata_flasher`

To build and upload the Snap package to the release candidate run

    snapcraft
    snapcraft upload --release=candidate inamata-flasher_x.x.x_amd64.snap

## Dependency Updates

When updating `littlefs-python` ensure that the generated LittleFS image matches or is lower than that supported by the firmware. The [Arduino-ESP32 GitHub repo][6] has the version currently used by the firmware. On [littlefs-python's pypi page][7] the compatible versions are listed.

## Internationalization

To translate strings, the Qt Linguist software is required. It can be installed as part of the Qt installer bundle or with the PySide6 Python package and then launched with the pyside6-linguist command.

The translations are saved in `ts` and `qm` files in the `translations` folder. The `ts` files act as the source files which the `qm` are the compiled versions loaded by the application itself. The strings are collected from the `uis/*.ui` and `src/*.py` files and stored in the `mainwindow_*.ts` and `main_*.ts` files respectively. Once collected, they can be translated with the QtLinguist application. Save the translated strings and then compile them to be used by the application itself. The workflow for German is given by the following commands. For the other languages, replace them with their language codes.

    ./build.sh i18n_u
    
    pyside6-linguist
    # Open the main_de_DE.ts and mainwindow_de_DE.ts files
    
    ./build.sh i18n_c

To delete translations that have become obesolete (in ts files but not found in source), run `./build.sh i18n` with `-P no_obsolete`. It is possible to open multiple translation files in parallel in PyLinguist. This allows the translation process to be streamlined. Simply shift select multiple files with the open file dialog.

## Build Options

While debugging the build process, it can be useful to only run build type, you can add the following options to `build.sh` to skip the respective build type.

- PyInstaller: `-P no_pyinstaller=1`
- Snap: `-P no_snap=1`
- Inno: `-P no_inno=1`

## Debugging Crashes

If the applications fails to start, two useful environment variables are

- QT_QPA_PLATFORM=xcb or QT_QPA_PLATFORM=wayland
- QPA_DEBUG_PLUGINS=1
