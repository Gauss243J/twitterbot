import tweepy
from django.conf import settings

# Function to fetch tweets from a user using Twitter API v2
def get_tweets_from_user(username, count=6):
    # Set up the tweepy client with Bearer Token for API v2
    print(settings.TWITTER_BEARER_TOKEN)
    print(settings.TWITTER_API_KEY)
    print(settings.TWITTER_API_SECRET_KEY)
    print(settings.TWITTER_ACCESS_TOKEN)
    print(settings.TWITTER_ACCESS_TOKEN_SECRET)
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

# Function to retweet a modified tweet
def retweet_with_modifications(tweet):
    # Set up the tweepy client again for posting a tweet
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

    # Post the modified tweet using API v2's create_tweet method
    client.create_tweet(text=modified_text)
