"""
A module that gets the imported modules from Python code.

-----------

Classes list:

No classes!

-----------

Functions list:

- get_imported(code: str) -> list[str]:

"""

from bundle_tools.create_logger import create_logger
import logging

logger = create_logger(name=__name__, level=logging.DEBUG)


def get_imported(code: str) -> list[str]:
    """
    Gets the imported modules from Python code.

    :param code: The code as a string.
    :return: A list of strings with the modules imported.
    """
    modules = []
    lines = code.splitlines()
    logger.debug(f"Found {len(lines)} lines in the code!")
    for line in lines:
        line = line.strip()
        while "  " in line:
            line = line.replace("  ", " ")
        parts = [part.strip() for part in line.split(sep=" ")]
        if parts[0] in ("import", "from"):
            logger.debug(f"Parts in import line: {repr(parts)}")
            if parts[0] == "import":
                if parts[1] not in modules:
                    modules.append(parts[1])
            else:
                module = f"{parts[1]}.{parts[3]}"
                if module not in modules:
                    modules.append(module)
    logger.debug(f"Modules imported in the code: {repr(modules)}")
    return modules
