# Togayo Flasher

Flash the firmware onto an ESP32 and register it with the server.

| Windows Screenshots                                   | Linux Screenshots                                      |
| ----------------------------------------------------- | ------------------------------------------------------ |
| ![Windows Welcome](screenshots/windows_welcome.png)   | ![Linux Welcome](screenshots/linux_add_controller.png) |
| The welcome page for Windows 10 → [more pages][1] | The add controller page for Ubuntu 20.04 → [more pages][2]     |

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
- Enable searching of combo boxes with many items
  - This is described on [StackOverflow](https://stackoverflow.com/questions/4827207/how-do-i-filter-the-pyqt-qcombobox-items-based-on-the-text-input)
- Use PlatformIO as an flash/upload tool?: https://community.platformio.org/t/upload-latest-build-without-a-compile-link/9520


[1]: screenshots/windows.md
[2]: screenshots/linux.md
[3]: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
[4]: https://www.silabs.com/documents/public/software/CP210x_Windows_Drivers.zip