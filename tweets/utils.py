import tweepy
import time
import requests
from urllib3.exceptions import ProtocolError
from django.conf import settings

import random

def get_tweets_from_user(username, count=6, retries=3):
    client = tweepy.Client(
        bearer_token=settings.TWITTER_BEARER_TOKEN,
        wait_on_rate_limit=True
    )

    try:
        user = client.get_user(username=username)
    except Exception as e:
        print(f"Error fetching user: {e}")
        return []

    if not user or not user.data:
        return []

    for attempt in range(retries):
        try:
            tweets_response = client.get_users_tweets(
                id=user.data['id'],
                max_results=count,
                expansions=['author_id'],
                user_fields=['username'],
                tweet_fields=['created_at'],
                exclude='replies',
            )
            if tweets_response.data:
                tweets = tweets_response.data
                users = {u.id: u for u in tweets_response.includes['users']}
                return tweets, users
            else:
                return []
        except (requests.exceptions.ConnectionError, ProtocolError) as e:
            print(f"Connection error (attempt {attempt + 1}): {e}")
            time.sleep(random.uniform(3, 7))  # pause entre 3 et 7 secondes avant de réessayer
        except Exception as e:
            print(f"Unexpected error: {e}")
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
        # Fetch your recent tweets (you can change the max_results to control how many tweets to check)
        user_tweets = client.get_users_tweets(id=settings.TWITTER_USER_ID, max_results=10)
        for tweet in user_tweets.data:
            if tweet['text'] == modified_text:
                return True
        return False
    except Exception as e:
        print(f"Error while checking existing tweets: {e}")
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

    # Modify the tweet text
    modified_text = modify_tweet_text(tweet,users)

    # Check if the tweet already exists
    if check_existing_tweet(client, modified_text):
        print("Tweet already exists. Skipping.")
        return  # Skip posting the tweet if it already exists

    # Post the modified tweet using API v2's create_tweet method
    try:
        client.create_tweet(text=modified_text)
        print(f"Tweet posted: {modified_text}")
    except tweepy.TooManyRequests as e:
        print(f"Rate limit exceeded. Sleeping for {e.retry_after} seconds.")
        time.sleep(e.retry_after)
    except (requests.exceptions.ConnectionError, ProtocolError) as e:
        print(f"Connection error encountered: {e}. Sleeping for 30 seconds before retrying...")
        time.sleep(30)
        try:
            client.create_tweet(text=modified_text)
            print(f"Tweet posted after retry: {modified_text}")
        except Exception as inner_e:
            print(f"Error posting tweet on retry: {inner_e}")
    except Exception as e:
        print(f"Error posting tweet: {e}")
