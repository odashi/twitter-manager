import logging
import random

from google.cloud import firestore

import utils

BATCH_SIZE = 45


def get_responded_users(tw_client, fs_client) -> set[str]:
    logger = logging.getLogger(__name__)

    user_ids: list[str] = []
    target_ids: list[str] = []

    for doc in fs_client.collection("target-users").stream():
        target_name = doc.id
        target_info = doc.to_dict()

        target_ids.append(str(target_info["twitter_id"]))

        response = tw_client.search_recent_tweets(
            f"to:{target_name}",
            max_results=int(target_info["replies"]),
            tweet_fields=["author_id"],
            user_auth=True,
        )

        replied_ids = [str(t.author_id) for t in response.data]
        user_ids += replied_ids
        logger.info(f"Replies to: {target_name}: {len(replied_ids)}")

    return set(user_ids) - set(target_ids)


blocked_users_cache = set()


def block_users() -> None:
    logger = logging.getLogger(__name__)

    tw_client = utils.make_twitter_client()
    fs_client = firestore.Client()

    collection = fs_client.collection("blocked-users")

    user_ids = list(get_responded_users(tw_client, fs_client))
    random.shuffle(user_ids)
    logger.info(f"Replied users: {len(user_ids)}")
    logger.info(f"Cache size: {len(blocked_users_cache)}")

    num_blocked = 0

    for i, user_id in enumerate(user_ids):
        if user_id in blocked_users_cache:
            logger.info(f"{i + 1}: Skip: {user_id} (cached)")
            continue
        
        doc = collection.document(str(user_id))
        
        if doc.get().exists:
            logger.info(f"{i + 1}: Skip: {user_id}")
        else:
            logger.info(f"{i + 1}: Block: {num_blocked + 1}: {user_id}")
            tw_client.block(user_id, user_auth=True)
            doc.set({})
            num_blocked += 1
            
        blocked_users_cache.add(user_id)

        if num_blocked >= BATCH_SIZE:
            return


def main(event, content) -> None:
    logger = logging.getLogger(__name__)
    
    try:
        block_users()
    except Exception as ex:
        logger.warning(f"Interrupted by an exception: {ex}")

        
utils.setup()

if utils.is_local_run():
    main(None, None)
