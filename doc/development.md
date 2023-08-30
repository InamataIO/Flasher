# Development Guide

## Start

1. Do the [driver setup](#driver-setup-instructions)
2. In a terminal run `poetry install`
3. Run `./start.sh` or `poetry run python src/main.py`

## Release Process

Push the final version (with updated version numbers), create a new release on Github, create a distributable binary for each platform and upload the releases to the Github release.

### Bump Version Numbers

Bump the version number in the following files

- [snap/snapcraft.yaml](../snap/snapcraft.yaml)
- [src/main.py](../src/main.py)
- [pyproject.toml](../pyproject.toml)

Tag the commit with

```bash
git tag v<version number>
git push
git push --tags
```

### Windows

After [obtaining](https://comodosslstore.com/codesigning.aspx) a code signing certificate, run the following commands:

    poetry install
    poetry shell
    pyinstaller main.spec
    # signtool.exe sign /tr http://timestamp.sectigo.com/ /td sha256 /fd sha256 /a C:\path\to\inamata_flasher.exe

The following instructions are useful to set up the [code signing key](https://stackoverflow.com/a/64499199/6783666) and install the [code signing tool](https://stackoverflow.com/questions/31869552/how-to-install-signtool-exe-for-windows-10).

A workaround is to preemptively submit the file for verification: https://stackoverflow.com/questions/48946680/how-to-avoid-the-windows-defender-smartscreen-prevented-an-unrecognized-app-fro/66582477#66582477

### Linux

Run the following command to create a PyInstaller distributable:

    poetry install
    poetry shell
    pyinstaller main.spec

The standalone executeable can be found in `dist/inamata_flasher`

## Dependency Updates

When updating `littlefs-python` ensure that the generated LittleFS image matches or is lower than that supported by the firmware. The [Arduino-ESP32 GitHub repo][6] has the version currently used by the firmware. On [littlefs-python's pypi page][7] the compatible versions are listed.