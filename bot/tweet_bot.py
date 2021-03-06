import locale
import logging
import os
from datetime import timedelta

import tweepy

from vaccination_stats import VaccinationStats

logger = logging.getLogger()


class TweetBot:
    def __init__(self, stats: VaccinationStats):
        self._stats = stats

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

    def tweet(self):
        """
        Create and send tweet with image
        """

        if not self.is_new_data():
            logger.info("No updates yet")
            return

        # Create Tweet
        locale.setlocale(locale.LC_ALL, "de_DE")
        status_text = (
            "In Deutschland sind {} Menschen ({}%) geimpft.\n"
            "Davon {} mit einer und {} mit zwei Impfungen.\n"
            "Impfungen/Tag: {} (Median über letzten 7 Meldetage)\n"
            "Stand: {}.".format(
                locale.format_string(
                    "%d", self._stats.vacc_cumulated, grouping=True, monetary=True
                ),
                locale.format_string(
                    "%.2f", self._stats.vacc_quote * 100, grouping=True, monetary=True
                ),
                locale.format_string(
                    "%d", self._stats.vacc_first, grouping=True, monetary=True
                ),
                locale.format_string(
                    "%d", self._stats.vacc_both, grouping=True, monetary=True
                ),
                locale.format_string(
                    "%d", self._stats.vacc_median, grouping=True, monetary=True
                ),
                self._stats.date.strftime("%d.%m.%Y"),
            )
        )

        from main import IMAGE  # Avoid Circular Import

        media = self._api.media_upload(IMAGE)
        self._api.update_status(
            status=status_text,
            lat=52.53988938917128,
            long=13.34704871422069,
            media_ids=[media.media_id],
        )

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

        if self._stats.date > last_dataset_date:
            return True

        return False
