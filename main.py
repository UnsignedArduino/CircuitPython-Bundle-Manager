import gui
from bundle_tools.create_logger import create_logger
import logging

logger = create_logger(name=__name__, level=logging.DEBUG)

logger.debug(f"Starting application...")
with gui.GUI() as gui:
    gui.run()  # Run GUI
logger.warning(f"Application stopped!")
