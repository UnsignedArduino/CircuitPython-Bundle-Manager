import gui
from bundle_tools.create_logger import create_logger
import logging

LEVEL = logging.DEBUG

logger = create_logger(name=__name__, level=LEVEL)

logger.debug(f"Starting application...")
logger.info(f"Log leve is {repr(LEVEL)}")
with gui.GUI() as gui:
    gui.run(log_level=LEVEL)  # Run GUI
logger.warning(f"Application stopped!")
