from pathlib import Path
from shutil import copy2, copytree


def get_lib_path(device_drive: Path = None) -> Path:
    return device_drive / "lib"


def list_modules(start_path: Path = None) -> list:
    lib_directory: Path = get_lib_path(start_path)
    if not lib_directory.exists():
        raise RuntimeError(f"The lib directory '{lib_directory}' does not exist on the CircuitPython device!")
    return list(lib_directory.glob("*"))


def install_module(module_path: Path, device_path: Path) -> None:
    if module_path.is_file():
        copy2(module_path, device_path)
    else:
        copytree(module_path, device_path / module_path.stem)


def uninstall_module(module_path: Path) -> None:
    if module_path.is_file():
        module_path.unlink()
    else:
        module_path.rmdir()
