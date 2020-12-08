from pathlib import Path
from typing import Union


def list_modules(start_path: Union[str, Path] = None) -> list:
    if not isinstance(start_path, str) and not isinstance(start_path, Path):
        raise TypeError(f"'start_path' is not of type 'str'. Got type: '{type(start_path)}' with value: '{start_path}'")
    lib_directory: Path = Path(start_path) / "lib"
    if not lib_directory.exists():
        raise RuntimeError(f"The lib directory '{lib_directory}' does not exist on the CircuitPython device!")
    return list(lib_directory.glob("*"))


def install_module(module_path: Path, device_path: Path) -> None:
    if not isinstance(module_path, Path):
        raise TypeError(f"'module_path' is not of type 'path'. "
                        f"Got type: '{type(module_path)}' with value: '{module_path}'")
    if not isinstance(device_path, Path):
        raise TypeError(f"'device_path' is not of type 'path'. "
                        f"Got type: '{type(device_path)}' with value: '{device_path}'")

