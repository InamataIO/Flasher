![Inamata Flasher](./images/header-logo.png)

Flash the firmware onto an ESP32 and register it with the server.

| Windows Screenshots                                 | Linux Screenshots                                      |
| ----------------------------------------------------| ------------------------------------------------------ |
| ![Windows Welcome](screenshots/windows_welcome.png) | ![Linux Welcome](screenshots/linux_add_controller.png) |
| Welcome page for Windows 10 → [more pages][1]       | Add controller page for Ubuntu 20.04 → [more pages][2] |

## Driver Setup Instructions

### Windows

Download and install the [CP210x USB to UART Bridge driver][4] for [silabs.com][3].

### Linux

Open a terminal, run the following code,  **logout** and then back in again for the changes to take effect.

    sudo usermod -a -G dialout $USER

On Ubuntu with Wayland, add `export QT_QPA_PLATFORM=xcb` to fix window borders.

To package the app see:
- https://github.com/taunoe/tauno-serial-plotter
- https://github.com/jordansissel/fpm/
- https://www.pythonguis.com/tutorials/packaging-pyqt5-applications-linux-pyinstaller/

## Future Features

This is a list of features that would be useful and show the tool's current limitations

- Handling of more than 100 site, firmware images or controller instances
  - This is due to not handling paging of the GraphQL requests
- Delete controller when creating a new on and an error occurs after registration
- Enable searching of combo boxes with many items
  - This is described on [StackOverflow](https://stackoverflow.com/questions/4827207/how-do-i-filter-the-pyqt-qcombobox-items-based-on-the-text-input)
- Use PlatformIO as an flash/upload tool?: https://community.platformio.org/t/upload-latest-build-without-a-compile-link/9520

## Release Process

Push the final version, create a new release on Github, create a distributable binary for each platform and upload the releases to the Github release.

### Windows

After [obtaining](https://comodosslstore.com/codesigning.aspx) a code signing certificate, run the following commands:

    pipenv install -d
    pipenv shell
    pyinstaller main.spec
    signtool.exe sign /tr http://timestamp.sectigo.com/ /td sha256 /fd sha256 /a C:\path\to\inamata_flasher.exe

The following instructions are useful to set up the [code signing key](https://stackoverflow.com/a/64499199/6783666) and install the [code signing tool](https://stackoverflow.com/questions/31869552/how-to-install-signtool-exe-for-windows-10).

### Linux

Run the following command to create a PyInstaller distributable:

    pipenv install -d
    pipenv shell
    pyinstaller main.spec


[1]: screenshots/windows.md
[2]: screenshots/linux.md
[3]: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
[4]: https://www.silabs.com/documents/public/software/CP210x_Windows_Drivers.zip
