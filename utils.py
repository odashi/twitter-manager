import logging
import os

from google.cloud import logging as cloud_logging
import tweepy


def is_local_run() -> bool:
    return os.environ.get("FUNCTION_TARGET") is None


def setup() -> None:
    if not is_local_run():
        cloud_logging.Client().setup_logging()

    logging.basicConfig(level=logging.INFO)


def make_twitter_client() -> tweepy.Client:
    return tweepy.Client(
        consumer_key=os.environ["TWITTER_CONSUMER_KEY"],
        consumer_secret=os.environ["TWITTER_CONSUMER_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
    )
