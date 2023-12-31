import re
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from semantic_version import Version


@dataclass
class Pattern:
    """Pattern for version files.

    Params:
        r: The regex to match the version line
        f: The f-string to replace the matched chars
    """

    r: str
    f: str

    def new_line(self, version: Version) -> str:
        return self.f.format(version=version)


class VersionFile(metaclass=ABCMeta):
    def __init__(self, root_path: Path):
        self.root_path = root_path

    @property
    @abstractmethod
    def path(self) -> Path:
        """The path to the version file."""

    @property
    @abstractmethod
    def patterns(self) -> list[Pattern]:
        """Regex pattern to match for."""

    def update_version(self, version: Version) -> None:
        with open(self.path, "r+") as f:
            data = f.read()
            f.seek(0)
            for pattern in self.patterns:
                re_pattern = re.compile(pattern.r, re.MULTILINE)
                data, _ = re.subn(re_pattern, pattern.new_line(version), data, 1)
            f.write(data)
            f.truncate()


class PyProjectFile(VersionFile):
    @property
    def path(self) -> Path:
        return self.root_path / Path("pyproject.toml")

    @property
    def patterns(self) -> list[Pattern]:
        return [Pattern(r=r'^version = ".*"$', f='version = "{version}"')]


class MainPyFile(VersionFile):
    @property
    def path(self) -> Path:
        return self.root_path / Path("src/main.py")

    @property
    def patterns(self) -> list[Pattern]:
        return [Pattern(r=r'^__version__ = ".*"$', f='__version__ = "{version}"')]


class SnapcraftFile(VersionFile):
    @property
    def path(self) -> Path:
        return self.root_path / Path("snap/snapcraft.yaml")

    @property
    def patterns(self) -> list[Pattern]:
        return [Pattern(r=r"^version: .*$", f="version: {version}")]


class InnoFile(VersionFile):
    @property
    def path(self) -> Path:
        return self.root_path / Path("publish/main.iss")

    @property
    def patterns(self) -> list[Pattern]:
        return [
            Pattern(r=r"^#define MyAppVersion .*$", f="#define MyAppVersion {version}")
        ]


class InfoFile(VersionFile):
    @property
    def path(self) -> Path:
        return self.root_path / Path("publish/windows/file_version_info.txt")

    @property
    def patterns(self) -> list[Pattern]:
        return [
            Pattern(
                r=r"filevers=\(.*\),$",
                f="filevers=({version.major}, {version.minor}, {version.patch}, 0),",
            ),
            Pattern(
                r=r"prodvers=\(.*\),$",
                f="prodvers=({version.major}, {version.minor}, {version.patch}, 0),",
            ),
            Pattern(
                r=r"StringStruct\('FileVersion', '.*\.windows'\),$",
                f="StringStruct('FileVersion', '{version}.windows'),",
            ),
            Pattern(
                r=r"StringStruct\('ProductVersion', '.*\.windows'\),$",
                f="StringStruct('ProductVersion', '{version}.windows'),",
            ),
        ]
