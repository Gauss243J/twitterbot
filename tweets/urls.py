from django.urls import path
from .views import process_tweets, twitter_callback, start_tweet_scraping


urlpatterns = [
    path('process_tweets/', process_tweets, name='process_tweets'),
    path('twitter/callback/', twitter_callback, name='twitter_callback'),
    path('scraping/', start_tweet_scraping, name='scraping'),
]

