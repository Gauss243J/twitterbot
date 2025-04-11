from django_cron import CronJobBase, Schedule
from django.utils import timezone
import requests

class TweetScrapingJob(CronJobBase):
    schedule = Schedule(run_every_mins=2880)  # 2880 minutes = 2 jours
    code = 'myapp.tweet_scraping_job'

    def do(self):
        url = "https://twitterbot-jk9g.onrender.com/tweets/process_tweets/"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                print(f"{timezone.now()}: Scraping des tweets terminé avec succès!")
            else:
                print(f"{timezone.now()}: Erreur lors du scraping des tweets.")
        except requests.exceptions.RequestException as e:
            print(f"{timezone.now()}: Erreur de connexion: {e}")

