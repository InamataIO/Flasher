![Togayo Flasher](./images/header-logo.png)

Flash the firmware onto an ESP32 and register it with the server.

## Driver Setup Instructions

### Windows

Download and install the [CP210x USB to UART Bridge driver][4] for [silabs.com][3].

### Linux

Open a terminal, run the following code,  **logout** and then back in again for the changes to take effect.

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

Push the final version, create a new release on Github, create a distributable binary for each platform and upload the releases to the Github release.

### Windows

TBD

### Linux

Run the following command to create a PyInstaller distributable:

    pipenv install -d
    pyinstaller main.spec


[1]: screenshots/windows.md
[2]: screenshots/linux.md
[3]: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
[4]: https://www.silabs.com/documents/public/software/CP210x_Windows_Drivers.zip
