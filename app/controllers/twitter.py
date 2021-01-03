import re
import requests
from loguru import logger
from sqlalchemy import *
import twint


class SVC_Twitter:
    @staticmethod
    def cmd_twitter(phrase, metadata, session):
        # phrase to be two parts: search by (keyword or username), the search argument
        search_by = phrase.split(", ")[0]
        keyword = phrase.split(", ")[1]
        try:
            config = twint.Config()
            if search_by == "username":
                config.Username = keyword
                body_text = "Tweets by: " + keyword + "\n"
            else:
                config.Search = keyword
                body_text = "Tweets about: " + keyword + "\n"
            config.Limit = 10  # running search
            config.Hide_output = True
            config.Store_object = True
            twint.run.Search(config)
            res = twint.output.tweets_list
            if len(res) > 0:
                limiter = 0
                body_text = "Tweets:\n"
                for tweet in res:
                    print(tweet)
                    limiter += 1
                    if limiter == 6:
                        break
                    else:
                        body_text += "Username: " + tweet.username
                        body_text += "\nDate: " + tweet.datetime
                        body_text += "\nTweet: " + tweet.tweet + "\n\n"
            else:
                body_text = "We didn't find any tweets about " + keyword + "."
        except Exception as e:
            print(e)
            body_text = "Error: " + str(e)
        return body_text
