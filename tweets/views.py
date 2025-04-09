from django.shortcuts import render
from django.http import JsonResponse
from .utils import get_tweets_from_user, retweet_with_modifications
from django.http import HttpResponse

# View to process tweets and repost them with modifications
def process_tweets(request):
    usernames = ['realfrance_fr', 'DivineProverbs']  # List of Twitter usernames
    for username in usernames:
        # Get the most recent tweets for the username
        tweets = get_tweets_from_user(username)
        for tweet in tweets:
            # Retweet each tweet with modifications
            retweet_with_modifications(tweet)
    
    # Render a callback page
    return render(request, 'tweets/success.html', {
        'message': 'Tweets processed and republished successfully.'
    })





def twitter_callback(request):
    return HttpResponse("Connexion réussie avec Twitter. Vous pouvez maintenant publier des tweets.")
