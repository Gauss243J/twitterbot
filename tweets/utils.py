import tweepy
import time
import requests
from urllib3.exceptions import ProtocolError
from django.conf import settings
import random
import logging

logger = logging.getLogger(__name__)


def get_tweets_from_user(username, count=5, retries=3):
    logger.debug(f"Fetching tweets for user: {username}")
    client = tweepy.Client(
        bearer_token=settings.TWITTER_BEARER_TOKEN,
        wait_on_rate_limit=True
    )

    try:
        user = client.get_user(username=username)
        logger.debug(f"User fetched: {user.data.username if user and user.data else 'None'}")
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        return ([], {})

    if not user or not user.data:
        logger.warning("User not found or has no data.")
        return ([], {})

    for attempt in range(retries):
        try:
            logger.debug(f"Attempt {attempt + 1} to fetch tweets for user {username}")
            tweets_response = client.get_users_tweets(
                id=user.data.id,
                max_results=count,
                expansions=['author_id'],
                user_fields=['username'],
                tweet_fields=['created_at'],
                exclude='replies',
            )
            if tweets_response.data:
                logger.debug(f"Fetched {len(tweets_response.data)} tweets for user {username}")
                tweets = tweets_response.data
                users = {u.id: u for u in tweets_response.includes['users']}
                return tweets, users
            else:
                logger.info(f"No tweets found for user: {username}")
                return ([], {})
        except (requests.exceptions.ConnectionError, ProtocolError) as e:
            logger.error(f"Connection error (attempt {attempt + 1}): {e}")
            time.sleep(random.uniform(3, 7))
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break
    logger.warning(f"All retries failed for user {username}")
    return ([], {})


def modify_tweet_text(tweet, users):
    author = users.get(tweet.author_id)
    modified = f"{tweet.text} @{author.username}" if author else f"{tweet.text} #SourceX"
    logger.debug(f"Modified tweet text: {modified}")
    return modified


def get_own_recent_tweet_texts():
    logger.debug("Fetching own recent tweets.")
    client = tweepy.Client(
        bearer_token=settings.TWITTER_BEARER_TOKEN,
        wait_on_rate_limit=True
    )
    try:
        response = client.get_users_tweets(id=settings.TWITTER_USER_ID, max_results=10)
        if response.data:
            texts = [tweet.text for tweet in response.data]
            logger.debug(f"Fetched recent tweet texts: {texts}")
            return texts
        else:
            logger.info("No recent tweets found.")
    except Exception as e:
        logger.error(f"Error fetching recent tweets: {e}")
    return []


def retweet_with_modifications(tweet, users, recent_texts):
    client = tweepy.Client(
        bearer_token=settings.TWITTER_BEARER_TOKEN,
        consumer_key=settings.TWITTER_API_KEY,
        consumer_secret=settings.TWITTER_API_SECRET_KEY,
        access_token=settings.TWITTER_ACCESS_TOKEN,
        access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=True
    )

    modified_text = modify_tweet_text(tweet, users)

    if modified_text in recent_texts:
        logger.info("Tweet already exists. Skipping.")
        return

    try:
        logger.debug(f"Posting tweet: {modified_text}")
        client.create_tweet(text=modified_text)
        logger.info(f"Tweet posted: {modified_text}")
    except tweepy.TooManyRequests as e:
        retry_after = getattr(e, 'retry_after', 900)
        logger.warning(f"Rate limit exceeded. Sleeping for {retry_after} seconds.")
        time.sleep(retry_after)
    except (requests.exceptions.ConnectionError, ProtocolError) as e:
        logger.error(f"Connection error encountered: {e}. Sleeping for 30 seconds before retrying...")
        time.sleep(30)
        try:
            client.create_tweet(text=modified_text)
            logger.info(f"Tweet posted after retry: {modified_text}")
        except Exception as inner_e:
            logger.error(f"Error posting tweet on retry: {inner_e}")
    except Exception as e:
        logger.error(f"Error posting tweet: {e}")
