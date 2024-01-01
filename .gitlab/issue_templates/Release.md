### Release Process

- [ ] Set issue and MR title as `<Major/Minor/Patch> release`
- [ ] Check if translations are up-to-date (`./build.sh i18n_u`)
- [ ] Run build script (`./build.sh -P bump=<major/minor/patch>`)
- [ ] Push commit and merge MR (no merge message)
- [ ] Tag squashed commit (`git tag vX.Y.Z && git push --tags`)
- [ ] Test on Linux VMs (Ubuntu 22.04, 20.04 and Kubuntu 22.04)
- [ ] Test on Linux Wayland session and X
- [ ] Create GitHub release with text (`./build.py text`)
- [ ] Upload Linux binaries
- [ ] Upload Windows binaries
- [ ] Promote Snap package to release channel

