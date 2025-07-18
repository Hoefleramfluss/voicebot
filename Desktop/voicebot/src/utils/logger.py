from loguru import logger
import sys

def setup_logger(target):
    logger.remove()
    if target == "console":
        logger.add(sys.stdout, level="INFO")
    elif target == "file":
        logger.add("logs/voicebot.log", level="INFO", rotation="10 MB")
    elif target == "webinterface":
        logger.add(sys.stdout, level="INFO")  # Platzhalter für Web-Log-Handler
    else:
        logger.add(sys.stdout, level="INFO")
