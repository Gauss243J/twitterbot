import tweepy
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

    # Fetch the recent tweets from the user
    tweets = client.get_users_tweets(id=user.data['id'], max_results=count)
    print(tweets)
    return tweets.data if tweets.data else []

# Function to modify the tweet text before reposting
def modify_tweet_text(tweet):
    return tweet['text'] + " #SourceX"

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
    except Exception as e:
        print(f"Error posting tweet: {e}")
