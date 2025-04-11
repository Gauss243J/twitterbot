import tweepy 
import time
import requests
from urllib3.exceptions import ProtocolError
from django.conf import settings
import random
import logging

logger = logging.getLogger(__name__)

# Function to fetch tweets from a user using Twitter API v2
def get_tweets_from_user(username, count=6, retries=3):
    client = tweepy.Client(
        bearer_token=settings.TWITTER_BEARER_TOKEN,
        wait_on_rate_limit=True
    )

    try:
        user = client.get_user(username=username)
    except Exception as e:
        logger.error(f"Error fetching user: {e}")
        return []

    if not user or not user.data:
        return []

    for attempt in range(retries):
        try:
            tweets_response = client.get_users_tweets(
                id=user.data.id,
                max_results=count,
                expansions=['author_id'],
                user_fields=['username'],
                tweet_fields=['created_at'],
                exclude='replies'
            )
            if tweets_response.data:
                tweets = tweets_response.data
                users = {u.id: u for u in tweets_response.includes['users']}
                return tweets, users
            else:
                return []
        except (requests.exceptions.ConnectionError, ProtocolError) as e:
            logger.error(f"Connection error (attempt {attempt + 1}): {e}")
            time.sleep(random.uniform(3, 7))  # Pause between 3 and 7 seconds before retrying
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break
    return []


# Function to modify the tweet text before reposting
def modify_tweet_text(tweet, users):
    author = users.get(tweet.author_id)
    if author:
        return f"{tweet.text} @{author.username}"
    else:
        return f"{tweet.text} #SourceX"


# Function to check if the tweet text already exists in your timeline
def check_existing_tweet(client, modified_text):
    try:
        user_tweets = client.get_users_tweets(id=settings.TWITTER_USER_ID, max_results=10)
        for tweet in user_tweets.data:
            if tweet.text == modified_text:
                return True
        return False
    except Exception as e:
        logger.error(f"Error while checking existing tweets: {e}")
        return False


# Function to retweet a modified tweet
def retweet_with_modifications(tweet, users):
    client = tweepy.Client(
        bearer_token=settings.TWITTER_BEARER_TOKEN,
        consumer_key=settings.TWITTER_API_KEY,
        consumer_secret=settings.TWITTER_API_SECRET_KEY,
        access_token=settings.TWITTER_ACCESS_TOKEN,
        access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=True
    )

    modified_text = modify_tweet_text(tweet, users)

    if check_existing_tweet(client, modified_text):
        logger.info("Tweet already exists. Skipping.")
        return  # Skip posting the tweet if it already exists

    try:
        client.create_tweet(text=modified_text)
        logger.info(f"Tweet posted: {modified_text}")
    except tweepy.TooManyRequests as e:
        logger.error(f"Rate limit exceeded. Sleeping for {e.retry_after} seconds.")
        time.sleep(e.retry_after)
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
