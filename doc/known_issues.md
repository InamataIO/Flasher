# Known Issues

## Windows

### COM port "access denied"

Only one program at a time may access a COM port. Therefore ensure that you do not have multiple instances of the Inamata Flasher running (check system monitor) and also no other programs such as PlatformIO (VS Code) have an open terminal.

## Linux

### Linux Wayland Crash

The session can be crashed when using Linux Wayland with mutter version <=42.5. This occurs when opening a dropdown / combo box and closing it by clicking outside the dropdown menu. This can be mitigated by one of the following:

- setting `QT_QPA_PLATFORM=xcb` in the environment variables
- using X11
- upgrading mutter in Ubuntu 22.04 through the [proposed packages][5]

[5]: https://wiki.ubuntu.com/Testing/EnableProposed

