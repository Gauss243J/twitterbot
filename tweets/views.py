from django.shortcuts import render
from django.http import HttpResponse
from .utils import get_tweets_from_user, retweet_with_modifications, get_own_recent_tweet_texts

# Vue pour traiter les tweets
def process_tweets(request):
    usernames = ['VibhorChandel', 'DivineProverbs']  # Liste des noms d'utilisateur Twitter
    recent_texts = get_own_recent_tweet_texts()  # Récupère les textes des tweets récents

    for username in usernames:
        # Récupère les tweets les plus récents pour l'utilisateur
        tweets, users = get_tweets_from_user(username)
        if not tweets:
            continue
        
        # Trie les tweets par date de création (du plus ancien au plus récent)
        sorted_tweets = sorted(tweets, key=lambda t: t.created_at)

        for tweet in sorted_tweets[:2]:
            # Retweeter chaque tweet avec des modifications
            retweet_with_modifications(tweet, users, recent_texts)  # Ajout de recent_texts

    # Rendre une page de succès après traitement
    return render(request, 'twitter/success.html', {
        'message': 'Tweets processed and republished successfully.'
    })

# Vue de callback pour la connexion Twitter
def twitter_callback(request):
    return HttpResponse("Connexion réussie avec Twitter. Vous pouvez maintenant publier des tweets.")
