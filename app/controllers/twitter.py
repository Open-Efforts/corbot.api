import re
import requests
from loguru import logger
from sqlalchemy import *
import snscrape.modules.twitter as sntwitter
import datetime

class SVC_Twitter:
    @staticmethod
    def cmd_twitter(phrase, metadata, session):
        # phrase to be two parts: search by (keyword or username), the search argument
        try:
            search_by = phrase.split(", ")[0]
            search_arg = phrase.split(", ")[1]
            todays_date_str = datetime.today().strftime('%Y-%m-%d')
            yesterdays_date = datetime.now() - timedelta(1)
            yesterdays_date_str = datetime.strftime(yesterdays_date, '%Y-%m-%d')
            if search_by == "keyword":
                scrape_crit = f"{search_arg} since:{yesterdays_date_str} until:{todays_date_str}"
                body_text = f"Tweets about {search_arg}:\n\n"

            elif search_by == "username":
                scrape_crit = f"from:{search_arg}"
                body_text = f"Tweets by {search_arg}:\n\n"

            # Using TwitterSearchScraper to scrape data and append tweets to list
            for i, tweet in enumerate(sntwitter.TwitterSearchScraper(scrape_crit).get_items()):
                # print(vars(tweet))
                # print(vars(tweet.user))
                if i > 9:
                    break
                date_str = tweet.date.strftime("%Y-%d-%m")
                body_text += f"Name: {tweet.user.displayname} ({tweet.user.username})\n"
                body_text += f"Date: {date_str}\n"
                body_text += f"Tweet: {tweet.content}\n\n"

        except Exception as e:
            body_text = "Error: " + str(e)
        print(body_text)
        return body_text
