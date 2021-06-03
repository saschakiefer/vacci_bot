import locale
import logging
import os
from datetime import timedelta

import tweepy
from PIL import Image, ImageDraw, ImageFont

from vaccination_stats import VaccinationStats

logger = logging.getLogger()


class TweetBot:
    IMAGE = "progress_bar.png"

    def __init__(self, stats: VaccinationStats):
        self._stats = stats

        locale.setlocale(locale.LC_ALL, "de_DE")

        # Authenticate to Twitter
        consumer_key = os.getenv("CONSUMER_KEY")
        consumer_secret = os.getenv("CONSUMER_SECRET")
        access_token = os.getenv("ACCESS_TOKEN")
        access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self._api = tweepy.API(
            auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True
        )
        self._api.verify_credentials()

        logger.info("Logged in to Twitter")

    def create_image(self):
        with Image.new("RGB", (1000, 500), color="#FEFFFE") as img:
            draw = ImageDraw.Draw(img)

            # Frame
            draw.rectangle([(25, 175), (975, 325)], width=2, outline="#000000")

            # Inner Bar
            draw.rectangle([(50, 200), (950, 300)], width=0, fill="#000000")

            # Draw 70%
            x = 50 + int(round(900 * 0.7))
            draw.line([(x, 200), (x, 300)], width=4, fill="green")

            # Draw current
            x = 50 + int(round(900 * self._stats.vacc_quote_first))
            draw.rectangle([(50, 200), (x, 300)], width=0, fill="#26a325")

            x = 50 + int(round(900 * self._stats.vacc_quote_complete))
            draw.rectangle([(50, 220), (x, 280)], width=0, fill="green")

            # Days to go
            fnt = ImageFont.truetype("bot/arial.ttf", 50)
            draw.text(
                (200, 220),
                "Days to {}%: {}".format(
                    str(int(self._stats.target_quote * 100)), str(self._stats.days_to_go)
                ),
                font=fnt,
                fill="white",
            )

            # Persons
            fnt = ImageFont.truetype("bot/arial.ttf", 18)
            draw.text(
                (204, 279),
                "{} people to go (first shot)".format(
                    locale.format_string(
                        "%d",
                        round(self._stats.people_to_go),
                        grouping=True,
                        monetary=True,
                    )
                ),
                font=fnt,
                fill="white",
            )

            # Target Date
            draw.text(
                (690, 279),
                self._stats.target_date.strftime("%d.%m.%Y"),
                font=fnt,
                fill="white",
            )

            img.save(TweetBot.IMAGE)

            logger.info("Image Created")

    def tweet(self, test_mode: bool = False):
        """
        Create and send tweet with image
        """

        if not test_mode and not self.is_new_data():
            logger.info("No updates yet")
            return

        # Create Tweet
        status_text = (
            "In Deutschland sind {} Menschen ({}%) geimpft.\n"
            "Davon {} ({}%) vollständig mit zwei Impfungen.\n"
            "Impfungen/Tag: {} (Median über letzten 7 Meldetage)\n"
            "Stand: {}.".format(
                locale.format_string(
                    "%d", self._stats.vacc_first, grouping=True, monetary=True
                ),
                locale.format_string(
                    "%.2f",
                    self._stats.vacc_quote_first * 100,
                    grouping=True,
                    monetary=True,
                ),
                locale.format_string(
                    "%d", self._stats.vacc_both, grouping=True, monetary=True
                ),
                locale.format_string(
                    "%.2f",
                    self._stats.vacc_quote_complete * 100,
                    grouping=True,
                    monetary=True,
                ),
                locale.format_string(
                    "%d", self._stats.vacc_median, grouping=True, monetary=True
                ),
                self._stats.date.strftime("%d.%m.%Y"),
            )
        )
        logger.info(status_text)

        self.create_image()

        if not test_mode:
            media = self._api.media_upload(TweetBot.IMAGE)
            self._api.update_status(
                status=status_text,
                lat=52.53988938917128,
                long=13.34704871422069,
                media_ids=[media.media_id],
            )
            logger.info("Tweeted")
        else:
            logger.info("Test mode. Nothing tweeted")

    def is_new_data(self) -> bool:
        """
        Check if the dataset is newer than at the last post.
        Since we run the bot in a docker container, we derive the date from
        the date of the last post. Thus we don;t have to care about persistence
        of "last run" date outside the container. The logic is for this bot
        good enough.
        :return: Is the dataset new?
        :rtype: bool
        """
        last_tweet = self._api.user_timeline(count=1)

        # Initially, there is no tweet, so for the first run always create one
        if len(last_tweet) == 0:
            return True

        # Logic: The dataset of a tweet is always from a day before, so if the
        # current dataset date is later than the tweet creation date - 1 day,
        # we create a new post. This should also work for weekends, or days
        # without new data
        last_dataset_date = (last_tweet[0].created_at - timedelta(days=1)).replace(
            hour=0, minute=0, second=0
        )
        logger.info(f"Last Tweet date is {last_tweet[0].created_at}")
        logger.info(f"Last dataset date is {last_dataset_date}")

        if self._stats.date > last_dataset_date:
            return True

        return False
