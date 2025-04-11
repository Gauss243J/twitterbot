import tweepy
import time
import requests
from urllib3.exceptions import ProtocolError
from django.conf import settings

# Function to fetch tweets from a user using Twitter API v2
def get_tweets_from_user(username, count=6):
    # Set up the tweepy client with Bearer Token for API v2
    client = tweepy.Client(
        bearer_token=settings.TWITTER_BEARER_TOKEN,
        wait_on_rate_limit=True  # This enables automatic waiting for rate limits
    )

    # Get the user ID (necessary for fetching tweets using API v2)
    user = client.get_user(username=username)
    if not user:
        return []

    # Fetch tweets including author info
    tweets_response = client.get_users_tweets(
        id=user.data['id'],
        max_results=count,
        expansions=['author_id'],
        user_fields=['username']
    )

    if not tweets_response.data:
        return []

    # Return both tweets and users in a format that supports sorting by created_at
    tweets = tweets_response.data
    users = {u.id: u for u in tweets_response.includes['users']}
    
    return tweets, users


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
def retweet_with_modifications(tweet):
    client = tweepy.Client(
        bearer_token=settings.TWITTER_BEARER_TOKEN,
        consumer_key=settings.TWITTER_API_KEY,
        consumer_secret=settings.TWITTER_API_SECRET_KEY,
        access_token=settings.TWITTER_ACCESS_TOKEN,
        access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=True
    )

    # Modify the tweet text
    modified_text = modify_tweet_text(tweet)

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
