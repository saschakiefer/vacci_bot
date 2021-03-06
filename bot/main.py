import logging
import sys

from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

from tweet_bot import TweetBot
from vaccination_stats import VaccinationStats

IMAGE = "progress_bar.png"

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
out_hdlr.setLevel(logging.INFO)
logger.addHandler(out_hdlr)
logger.setLevel(logging.DEBUG)


def create_chart(stats: VaccinationStats):
    with Image.new("RGB", (1000, 200), color="#FEFFFE") as img:
        draw = ImageDraw.Draw(img)

        # Frame
        draw.rectangle([(25, 25), (975, 175)], width=2, outline="#000000")

        # Inner Bar
        draw.rectangle([(50, 50), (950, 150)], width=0, fill="#000000")

        # Draw 70%
        x = 50 + int(round(900 * 0.7))
        draw.line([(x, 50), (x, 150)], width=4, fill="green")

        # Draw current
        x = 50 + int(round(900 * stats.vacc_quote))
        draw.rectangle([(50, 50), (x, 150)], width=0, fill="green")

        # Days to go
        fnt = ImageFont.truetype("bot/arial.ttf", 50)
        draw.text(
            (200, 70), "Days to 70%: " + str(stats.days_to_go), font=fnt, fill="white"
        )

        img.save(IMAGE)

        logger.info("Image Created")


if __name__ == "__main__":
    logger.info(f"Started")
    load_dotenv(verbose=True)

    try:
        dataset = VaccinationStats()
        create_chart(dataset)
        TweetBot(dataset).tweet()
    except Exception as ex:
        logger.error("Error executing the bot", exc_info=True)
        logger.info("Finished with error")
        raise ex

    logger.info(f"Successfully ended")
