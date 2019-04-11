import logging
import os

IS_DEBUGGING = str(os.environ.get("DEBUGGING", "no")).strip().lower() == "yes"
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG if IS_DEBUGGING else logging.INFO)
LOGGER.debug("Loading lambda...")


def hello_world_handler(event, context):
    LOGGER.debug("Running hello world...")
    LOGGER.info("Hello World!")
    LOGGER.info("Successfully ran hello world.")
