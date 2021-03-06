import logging
import sys

from dotenv import load_dotenv

from tweet_bot import TweetBot
from vaccination_stats import VaccinationStats

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
out_hdlr.setLevel(logging.INFO)
logger.addHandler(out_hdlr)
logger.setLevel(logging.DEBUG)


if __name__ == "__main__":
    logger.info("Started")

    test_mode = False
    if "--test" in sys.argv:
        test_mode = True

    logger.info(f"Test mode: {test_mode}")

    load_dotenv(verbose=True)

    try:  # Global Error Handling
        dataset = VaccinationStats()
        TweetBot(dataset).tweet(test_mode=test_mode)
    except Exception as ex:
        logger.error("Error executing the bot", exc_info=True)
        logger.info("Finished with error")
        raise ex

    logger.info("Successfully ended")
