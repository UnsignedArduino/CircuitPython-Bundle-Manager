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


def get_imported(code: str) -> tuple[list[str], list[str]]:
    """
    Gets the imported modules from Python code.

    :param code: The code as a string.
    :return: A tuple of a list of strings with the modules imported. The first list is the module name, the second list
      is the line that the imported module was imported.
    """
    modules = []
    module_lines = []
    lines = code.splitlines()
    logger.debug(f"Found {len(lines)} lines in the code!")
    for line in lines:
        line = line.strip()
        while "  " in line:
            line = line.replace("  ", " ")
        line = line.replace(",", "")
        parts = [part.strip() for part in line.split(sep=" ")]
        if parts[0] in ("import", "from"):
            logger.debug(f"Parts in import line: {repr(parts)}")
            if parts[0] == "import":
                if parts[1] not in modules:
                    modules.append(parts[1])
            else:
                module = parts[1]
                if module not in modules:
                    modules.append(module)
            module_lines.append(line)
    logger.debug(f"Modules imported in the code: {repr(modules)}")
    logger.debug(f"Lines: {repr(module_lines)}")
    return modules, module_lines
