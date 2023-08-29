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

### Building Snap

The error `Failed to refresh package list: failed to run apt update.` when building snaps with snapcraft means that the LXC container can not connect to the internet. This may be caused by Docker, another containerization technology. To fix it run:

```
# Stop Docker (may be started again after LXC is running)
sudo systemctl stop docker
sudo systemctl stop docker.socket

# Set accept all policy to all connections
sudo iptables -P INPUT ACCEPT && sudo iptables -P OUTPUT ACCEPT && sudo iptables -P FORWARD ACCEPT

# Delete all existing rules
sudo iptables -F INPUT && sudo iptables -F OUTPUT && sudo iptables -F FORWARD
```

[5]: https://wiki.ubuntu.com/Testing/EnableProposed

