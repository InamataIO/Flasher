![Apache2.0](https://img.shields.io/github/license/InamataCo/Flasher)
![GitHub tag (with filter)](https://img.shields.io/github/v/tag/InamataCo/Flasher)
![Linux Support](https://img.shields.io/badge/OS-Linux-dark_green)
![Windows Support](https://img.shields.io/badge/OS-Windows-dark_green)

[![Inamata Logo](images/inamata_logo.png)][10]

# Inamata Flasher

Flash the firmware onto an ESP32 and register it with the server. Released for the [Inamata IoT platform][10].

## Download

[![Get it from the Snap Store](https://snapcraft.io/static/images/badges/en/snap-store-white.svg)](https://snapcraft.io/inamata-flasher)

For Windows download the [latest release][8].

For Linux use the [Snap download][9] to receive automatic updates.

The app is available from the following sources:

|              | GitHub Release | Snap Store | Source |
| ------------ | -------------- | ---------- | ------ |
| **Linux**    | Yes            | Yes        | Yes    |
| **Windows**  | Yes            | No         | Yes    |
| **Packaged** | PyInstaller    | Snap       | No     |

## Start

1. Do the [driver setup](#driver-setup-instructions)
2. In a terminal run `pipenv install --dev`
3. Run `./start.sh`

## Screenshots

| Windows Screenshots                                 | Linux Screenshots                                      |
| --------------------------------------------------- | ------------------------------------------------------ |
| ![Windows Welcome](screenshots/windows_welcome.png) | ![Linux Welcome](screenshots/linux_add_controller.png) |
| Welcome page for Windows 10 → [more pages][1]       | Add controller page for Ubuntu 22.04 → [more pages][2] |

## Snap Setup Instructions

Snap isolates apps so it requires explicit permission to access USB devices to flash microcontrollers as well as optionally saving the authentication token. Run the following commands in a terminal:

```
snap connect inamata-flasher:raw-usb
```

Optionally, to enable saving the authentication token between restarts:

```
snap connect inamata-flasher:password-manager-service
```

## Driver Setup Instructions

### Windows

Download and install the [CP210x USB to UART Bridge driver][4] for [silabs.com][3].

### Linux

Open a terminal, run the following code, **logout** and then back in again for the changes to take effect.

    sudo usermod -a -G dialout $USER

## Future Features

This is a list of features that would be useful and show the tool's current limitations

- Handling of more than 100 site, firmware images or controller instances
  - This is due to not handling paging of the GraphQL requests
- Delete controller when creating a new on and an error occurs after registration
- Enable searching of combo boxes with many items
  - This is described on [StackOverflow](https://stackoverflow.com/questions/4827207/how-do-i-filter-the-pyqt-qcombobox-items-based-on-the-text-input)
- Use PlatformIO as an flash/upload tool?: https://community.platformio.org/t/upload-latest-build-without-a-compile-link/9520

## Release Process

Push the final version (with updated version numbers), create a new release on Github, create a distributable binary for each platform and upload the releases to the Github release.

### Bump Version Numbers

Bump the version number in the following files

- [snap/snapcraft.yaml](snap/snapcraft.yaml)
- [src/main.py](src/main.py)
- [pyproject.toml](pyproject.toml)

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

## Known Issues

### Linux Wayland Crash

The session can be crashed when using Linux Wayland with mutter version <=42.5. This occurs when opening a dropdown / combo box and closing it by clicking outside the dropdown menu. This can be mitigated by one of the following:

- setting `QT_QPA_PLATFORM=xcb` in the environment variables
- using X11
- upgrading mutter in Ubuntu 22.04 through the [proposed packages][5]

[1]: screenshots/windows.md
[2]: screenshots/linux.md
[3]: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
[4]: https://www.silabs.com/documents/public/software/CP210x_Windows_Drivers.zip
[5]: https://wiki.ubuntu.com/Testing/EnableProposed
[6]: https://github.com/espressif/arduino-esp32/blob/master/libraries/LittleFS/library.properties
[7]: https://pypi.org/project/littlefs-python/
[8]: https://github.com/InamataCo/Flasher/releases/latest
[9]: https://snapcraft.io/inamata-flasher
[10]: https://www.inamata.co
