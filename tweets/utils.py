import tweepy 
import time
import random
import logging
from urllib3.exceptions import ProtocolError
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialiser le client une seule fois et l'utiliser pour toutes les fonctions
client = tweepy.Client(
    bearer_token=settings.TWITTER_BEARER_TOKEN,
    consumer_key=settings.TWITTER_API_KEY,
    consumer_secret=settings.TWITTER_API_SECRET_KEY,
    access_token=settings.TWITTER_ACCESS_TOKEN,
    access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
    wait_on_rate_limit=True
)

# Cache des utilisateurs et de leurs tweets pour éviter de faire des appels répétitifs
user_cache = {}
tweets_cache = {}

# Fonction pour récupérer les tweets d'un utilisateur, avec un cache
def get_tweets_from_user(username, count=5, retries=3):
    if username in tweets_cache:
        logger.debug(f"Using cached tweets for user: {username}")
        return tweets_cache[username]

    logger.debug(f"Fetching tweets for user: {username}")
    if username not in user_cache:
        try:
            user = client.get_user(username=username)
            logger.debug(f"User fetched: {user.data.username if user and user.data else 'None'}")
            if user and user.data:
                user_cache[username] = user.data
            else:
                logger.warning(f"User {username} not found.")
                return [], {}
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            return [], {}

    user = user_cache[username]
    for attempt in range(retries):
        try:
            logger.debug(f"Attempt {attempt + 1} to fetch tweets for user {username}")
            tweets_response = client.get_users_tweets(
                id=user.id,
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
                tweets_cache[username] = (tweets, users)
                return tweets, users
            else:
                logger.info(f"No tweets found for user: {username}")
                return [], {}
        except (requests.exceptions.ConnectionError, ProtocolError) as e:
            logger.error(f"Connection error (attempt {attempt + 1}): {e}")
            time.sleep(random.uniform(3, 7))
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            break
    logger.warning(f"All retries failed for user {username}")
    return [], {}

# Fonction pour récupérer les derniers tweets du compte avec une gestion améliorée du cache
def get_own_recent_tweet_texts():
    logger.debug("Fetching own recent tweets.")
    # Cache les tweets récents pour éviter des appels répétitifs
    if 'own_recent_tweets' in tweets_cache:
        return tweets_cache['own_recent_tweets']

    username = settings.TWITTER_USER_ID
    try:
        user = client.get_user(username=username)
        logger.debug(f"L'ID de l'utilisateur {username} est : {user.data.id}")
        response = client.get_users_tweets(id=user.data.id, max_results=5)
        if response.data:
            texts = [tweet.text for tweet in response.data]
            logger.debug(f"Fetched recent tweet texts: {texts}")
            tweets_cache['own_recent_tweets'] = texts
            return texts
        else:
            logger.info("No recent tweets found.")
    except Exception as e:
        logger.error(f"Error fetching recent tweets: {e}")
    return []

# Fonction pour republier les tweets avec des modifications
def retweet_with_modifications(tweet, users, recent_texts):
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
        try:
            client.create_tweet(text=modified_text)
            logger.info(f"Tweet posted after retry: {modified_text}")
        except Exception as inner_e:
            logger.error(f"Error posting tweet on retry: {inner_e}")
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

