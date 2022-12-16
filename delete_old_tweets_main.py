import datetime
import logging

from google.cloud import firestore

import utils

THRESHOLD_DAYS = 3
BATCH_SIZE = 25


def main(event, content) -> None:
    logger = logging.getLogger(__name__)

    tw_client = utils.make_twitter_client()
    fs_client = firestore.Client()

    collection = fs_client.collection("deleted-tweets")

    my_id = tw_client.get_me().data.id
    threshold = datetime.datetime.now() - datetime.timedelta(days=THRESHOLD_DAYS)

    tweets = tw_client.get_users_tweets(
        my_id,
        max_results=BATCH_SIZE,
        end_time=threshold,
        tweet_fields=["created_at"],
        user_auth=True,
    ).data

    if tweets:
        for tweet in tweets:
            logger.info(f"Delete: id={tweet.id}, created_at={tweet.created_at}")
            tw_client.delete_tweet(tweet.id)
            data = {k: v for k, v in tweet.data.items() if k != "id"}
            collection.document(str(tweet.id)).set({"data": data})
    else:
        logger.info("No tweet to delete.")


utils.setup()

if utils.is_local_run():
    main(None, None)
