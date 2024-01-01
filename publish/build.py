import copy
import glob
import os
import re
import shutil
import subprocess
from logging import Logger
from pathlib import Path

from pybuilder.core import Project, init, task
from pybuilder.errors import PyBuilderException
from semantic_version import Version
from version_updaters import (
    InfoFile,
    InnoFile,
    MainPyFile,
    PyProjectFile,
    SnapcraftFile,
    VersionFile,
)

default_task = ["build"]


@init
def a_set_paths(project: Project):
    """Group A: Set all project relevant paths."""

    root_dir = Path(".").absolute()
    project.set_property("root_dir", root_dir)

    # Directors / Folders
    build_dir = root_dir / "build"
    project.set_property("build_dir", build_dir)
    dist_dir = root_dir / "dist"
    project.set_property("dist_dir", dist_dir)
    work_dirs = [build_dir, dist_dir]
    project.set_property("work_dirs", work_dirs)

    # Dist files
    pyinstaller_target = dist_dir / "inamata_flasher"
    project.set_property("pyinstaller_target", pyinstaller_target)
    snap_files = [root_dir / i for i in glob.glob("inamata-flasher_*.snap")]
    project.set_property("snap_files", snap_files)

    # PyInstaller files
    pyinstaller_one_file = root_dir / "publish/one-file.spec"
    project.set_property("pyinstaller_one_file", pyinstaller_one_file)
    pyinstaller_one_dir = root_dir / "publish/one-dir.spec"
    project.set_property("pyinstaller_one_dir", pyinstaller_one_dir)

    # Inno Setup files
    iss_file = root_dir / "publish/main.iss"
    project.set_property("iss_file", iss_file)
    iscc_file = os.getenv("ISCC_PATH", "/c/Program Files (x86)/Inno Setup 6/ISCC.exe")
    project.set_property("iscc_file", iscc_file)

    # Version files
    version_files = [
        PyProjectFile(root_dir),
        MainPyFile(root_dir),
        SnapcraftFile(root_dir),
        InnoFile(root_dir),
        InfoFile(root_dir),
    ]
    project.set_property("version_files", version_files)


@init
def a_set_versions(project: Project):
    """Group A: set current and next version numbers."""

    current_version_tag = (
        subprocess.run("git describe --tags".split(), capture_output=True)
        .stdout.decode()
        .strip()
    )
    current_version = Version(current_version_tag[1:].split("-")[0])
    project.set_property("current_version", current_version)

    clean = not subprocess.run("git status -s".split(), capture_output=True).stdout

    # Increment the version number
    if bump := project.get_property("bump"):
        if not clean:
            raise PyBuilderException("Repo must be clean when bumping version")
        match bump:
            case "major" | "ma":
                next_version = current_version.next_major()
            case "minor" | "mi":
                next_version = current_version.next_minor()
            case "patch" | "pa":
                next_version = current_version.next_patch()
            case _ as bump:
                raise PyBuilderException(
                    f"Invalid bump version: {bump}. Use major/minor/patch"
                )
    else:
        # Mark version as dev if not bumping for release
        next_version = copy.copy(current_version)
        commit = (
            subprocess.run("git rev-parse --short HEAD".split(), capture_output=True)
            .stdout.decode()
            .strip()
        )
        clean_str = "clean" if clean else "dirty"
        next_version.prerelease = ("dev", f"{commit}_{clean_str}")
    project.set_property("next_version", next_version)


@init
def b_set_pyinstaller_params(project: Project):
    """Group B: Set base PyInstaller parameters."""

    params = [
        "poetry",
        "run",
        "pyinstaller",
        "--distpath",
        str(project.get_mandatory_property("dist_dir")),
        "--workpath",
        str(project.get_mandatory_property("build_dir")),
        "-y",
    ]
    project.set_property("pyinstaller_base_params", params)


def clean_python_env(logger: Logger):
    logger.info("Cleaning Python venv")
    env = os.environ.copy()
    env.pop("PYTHONPATH")
    lock_cmd = "poetry lock --no-update"
    completed_ps = subprocess.run(lock_cmd.split(), env=env)
    if completed_ps.returncode:
        raise PyBuilderException(f"Failed locking Poetry ({lock_cmd})")
    sync_cmd = "poetry install --sync --with dev"
    completed_ps = subprocess.run(sync_cmd.split(), env=env)
    if completed_ps.returncode:
        raise PyBuilderException(f"Failed cleaning Poetry ({sync_cmd})")


def clean_build_files(project: Project, logger: Logger):
    logger.info("Deleting build files")
    root_dir: Path = project.get_mandatory_property("root_dir")
    for dir in project.get_property("work_dirs", []):
        try:
            shutil.rmtree(dir)
        except FileNotFoundError:
            continue
        logger.info(f"Deleted build dir: {dir.relative_to(root_dir)}")

    for file in project.get_property("snap_files", []):
        os.remove(file)
        logger.info(f"Deleted Snap file: {file.relative_to(root_dir)}")


def compile_translations(project: Project, logger: Logger):
    logger.info("Compiling translations")
    root_dir: Path = project.get_mandatory_property("root_dir")
    compile_sh = root_dir / "publish" / "compile_translations.sh"
    subprocess.run([str(compile_sh.absolute())])


def update_translations(project: Project, logger: Logger):
    logger.info("Updating translations")
    root_dir: Path = project.get_mandatory_property("root_dir")
    update_sh = root_dir / "publish" / "update_translations.sh"
    command = [str(update_sh.absolute())]
    if project.has_property("no_obsolete"):
        command.append("-no-obsolete")
    subprocess.run(command)


def build_linux_pyinstaller(project: Project, logger: Logger):
    logger.info("Starting PyInstaller Linux one-file build")
    next_version = project.get_mandatory_property("next_version")
    base_params = project.get_mandatory_property("pyinstaller_base_params")
    pyinstaller_one_file = project.get_mandatory_property("pyinstaller_one_file")
    subprocess.run([*base_params, str(pyinstaller_one_file)])

    versioned_name = f"inamata_flasher-{next_version}-linux-x86_64"
    linux_name = "inamata_flasher-linux-x86_64"
    root_dir = project.get_mandatory_property("root_dir")
    pyinstaller_target: Path = project.get_mandatory_property("pyinstaller_target")
    dist_dir: Path = project.get_mandatory_property("dist_dir")
    versioned_path = dist_dir / versioned_name
    linux_path = dist_dir / linux_name
    shutil.copyfile(pyinstaller_target, dist_dir / versioned_name)
    shutil.copyfile(pyinstaller_target, dist_dir / linux_name)

    logger.info(f"PyInstaller dist file: {pyinstaller_target.relative_to(root_dir)}")
    logger.info(f"PyInstaller dist file: {versioned_path.relative_to(root_dir)}")
    logger.info(f"PyInstaller dist file: {linux_path.relative_to(root_dir)}")


def build_windows_pyinstaller(project: Project, logger: Logger):
    logger.info("Starting PyInstaller Windows one-file build")
    next_version = project.get_mandatory_property("next_version")
    base_params = project.get_mandatory_property("pyinstaller_base_params")
    pyinstaller_one_file = project.get_mandatory_property("pyinstaller_one_file")
    subprocess.run([*base_params, str(pyinstaller_one_file)])

    versioned_name = f"inamata_flasher-{next_version}-windows-x86_64"
    linux_name = "inamata_flasher-windows-x86_64"
    root_dir = project.get_mandatory_property("root_dir")
    pyinstaller_target: Path = project.get_mandatory_property("pyinstaller_target")
    dist_dir: Path = project.get_mandatory_property("dist_dir")
    versioned_path = dist_dir / versioned_name
    linux_path = dist_dir / linux_name
    shutil.copyfile(pyinstaller_target, dist_dir / versioned_name)
    shutil.copyfile(pyinstaller_target, dist_dir / linux_name)

    logger.info(f"PyInstaller dist file: {pyinstaller_target.relative_to(root_dir)}")
    logger.info(f"PyInstaller dist file: {versioned_path.relative_to(root_dir)}")
    logger.info(f"PyInstaller dist file: {linux_path.relative_to(root_dir)}")


def build_snap(project: Project, logger: Logger):
    # logger.info("Stopping Docker and reseting iptables")
    # # Stop Docker (may be started again after LXC is running)
    # subprocess.run("sudo systemctl stop docker".split())
    # subprocess.run("sudo systemctl stop docker.socket".split())
    # # Set accept all policy to all connections
    # subprocess.run("sudo iptables -P INPUT ACCEPT".split())
    # subprocess.run("sudo iptables -P OUTPUT ACCEPT".split())
    # subprocess.run("sudo iptables -P FORWARD ACCEPT".split())
    # # Delete all existing rules
    # subprocess.run("sudo iptables -F INPUT".split())
    # subprocess.run("sudo iptables -F OUTPUT".split())
    # subprocess.run("sudo iptables -F FORWARD".split())
    # # Reset supo permission
    # subprocess.run("sudo -K".split(" "))

    logger.info("Building Snap package")
    subprocess.run(["snapcraft"])

    snap_files: list[Path] = project.get_mandatory_property("snap_files")
    dist_dir: Path = project.get_mandatory_property("dist_dir")
    root_dir: Path = project.get_mandatory_property("root_dir")
    for file in snap_files:
        new_path = shutil.move(file, dist_dir / file.name)
        rel_path = Path(new_path).relative_to(root_dir)
        logger.info(f"Snap dist file: {rel_path}")


def build_inno(project: Project, logger: Logger):
    logger.info("Building the Inno Setup package")
    base_params = project.get_mandatory_property("pyinstaller_base_params")
    pyinstaller_one_dir = project.get_mandatory_property("pyinstaller_one_dir")
    subprocess.run([*base_params, str(pyinstaller_one_dir)])

    iss_file: Path = project.get_mandatory_property("iss_file")
    windows_iss_path = subprocess.run(
        ["cygpath", "-w", iss_file.absolute()], capture_output=True
    ).stdout.decode()
    iscc_file = project.get_mandatory_property("iscc_file")
    subprocess.run([str(iscc_file), windows_iss_path])


def update_version_files(project: Project, logger: Logger):
    version_files: list[VersionFile] = project.get_mandatory_property("version_files")
    root_dir = project.get_mandatory_property("root_dir")
    for file in version_files:
        logger.info(f"Updating version in: {file.path.relative_to(root_dir)}")
        file.update_version(project.get_mandatory_property("next_version"))


@task(description="Build binaries for current platform.")
def build(project: Project, logger: Logger):
    # Print build info
    next_version: Version = project.get_mandatory_property("next_version")
    logger.info(f"Next version: {next_version}")
    logger.info(f"Target OS: {os.name}")

    clean_python_env(logger)

    bump_and_commit = not next_version.prerelease
    if bump_and_commit:
        update_version_files(project, logger)
    else:
        logger.info(
            "Skipping version bump as not specified (-P bump=<major/minor/patch)"
        )

    compile_translations(project, logger)

    if not project.has_property("no_pyinstaller"):
        if os.name == "posix":
            build_linux_pyinstaller(project, logger)
        else:
            build_windows_pyinstaller(project, logger)

    if os.name == "posix":
        if not project.has_property("no_snap"):
            build_snap(project, logger)
    else:
        if not project.has_property("no_inno"):
            build_inno(project, logger)

    if bump_and_commit:
        subprocess.run("git add .".split())
        commit_title = f"Release {next_version}"
        subprocess.run(["git", "commit", "-m", f"{commit_title}"])
        logger.info(f"Release tag : v{next_version}")


@task(description="Sync Poetry and delete build / dist files.")
def clean(project: Project, logger: Logger):
    clean_python_env(logger)
    clean_build_files(project, logger)


@task(description="Update translations from source files.")
def i18n_u(project: Project, logger: Logger):
    update_translations(project, logger)


@task(description="Compile translations for run-time.")
def i18n_c(project: Project, logger: Logger):
    compile_translations(project, logger)


@task(description="Generate text for GitHub release")
def text():
    last_tag = (
        subprocess.run(
            "git describe HEAD~ --abbrev=0 --tags".split(), capture_output=True
        )
        .stdout.decode()
        .strip()
    )
    output = (
        subprocess.run(
            [
                "git",
                "--no-pager",
                "log",
                "--pretty=format:'### %s%n%n%b'",
                f"{last_tag}..HEAD",
            ],
            capture_output=True,
        )
        .stdout.decode()
        .strip()
    )
    # Remove leading and trailing ' (apostrophes)
    output = output[1:-1]
    output = output.replace("'\n'", "\n")
    # Remove checklist and closes text
    commit_suffix = re.compile(r"\nChecklist:[\S\s]+?Closes #\d+\n")
    output = re.sub(commit_suffix, "", output)
    print(output)
