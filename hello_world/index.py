import logging
import os

IS_DEBUGGING = "debugging" in os.environ and os.environ["debugging"] == "yes"

logging.basicConfig(level=logging.DEBUG if IS_DEBUGGING else logging.INFO,
                    format="%(asctime)s %(levelname)-8s %(message)s")
LOGGER = logging.getLogger()
LOGGER.debug("Loading lambda...")


def hello_world_handler(event, context):
    LOGGER.debug("Running hello world...")
    LOGGER.info("Hello World!")
    LOGGER.debug("Successfully ran hello world.")
