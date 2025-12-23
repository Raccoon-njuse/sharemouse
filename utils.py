import logging
import sys

def setup_logging(level=logging.INFO):
    """Configures the logging for the application."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("ShareMouse")

logger = setup_logging()
