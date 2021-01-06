from loguru import logger
from sqlalchemy import Table
from .google import SVC_Google
import feedparser


from app import metadata, session


class SVC_RSS:
    def cmd_rss(arg):
        text_data = ""
        chan = str(arg)
        channel_list = SVC_RSS.chan_list(metadata, session)
        go = 1
        try:
            chan = int(chan)
            logger.info("Converting to Integer")
        except:
            go = 0
            text_data += "The feed you selected can not be found. Please choose from one of the feeds listed below: [EOL]"
            text_data += SVC_RSS.show_chans(metadata, session)
            logger.info("Failed to Convert to Integer")

        if isinstance(chan, int):
            chan = chan
        else:
            go = 0
            text_data = "The feed you selected can not be found. Please choose from one of the feeds listed below: [EOL]"
            text_data += SVC_RSS.show_chans(metadata, session)
            logger.info("Is Not an Integer")

        if go == 1:
            if chan > (len(channel_list) + 1):
                go = 0
                text_data = "The feed you selected can not be found. Please choose from one of the feeds listed below: [EOL]"
                text_data += SVC_RSS.show_chans(metadata, session)
                logger.info("Feed Number too High")
            else:
                logger.info("Feed Number Found: Processing.")
                ##############################
                chan_data = SVC_RSS.chan_data(chan, metadata, session)
                #############################
                rss_url = chan_data["feed_url"]
                if chan != 32:
                    feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.85 Safari/537.36"
                d = feedparser.parse(rss_url)
                text_data = d["feed"]["title"] + "[EOL]"
                text_data += "Home Page: " + d["feed"]["link"] + "[EOL]"
                text_data += (
                    "-----------------------------------------------------[EOL]"
                )
                entry_cnt = len(d["entries"])
                for post in d.entries:
                    try:
                        text_data += post.title + "[EOL]"
                    except:
                        pass
                    try:
                        text_data += post.published + "[EOL]"
                    except:
                        pass
                    link_url = post.link
                    text_data += "URL: " + post.link + "[EOL]"
                    link_code = SVC_Google.proc_link(link_url, metadata, session)
                    text_data += "Link Code: " + link_code + "[EOL]"
                    try:
                        summary = post.summary
                        pos1 = summary.find(">") + 1
                        if pos1 > 0:
                            summary = summary[pos1:]
                            pos2 = summary.find("<") + 1
                            summary = summary[: pos2 - 1]
                        text_data += summary.strip() + "[EOL]"
                    except:
                        pass
                    text_data += "-------------------------[EOL]"
                    text_data = text_data.replace("[EOL]", "\r\n")
        return text_data

    def chan_data(chan, metadata, session):
        rss_feeds = Table("rss_feeds", metadata, autoload=True)
        qry = rss_feeds.select().where(rss_feeds.c.feed_id == chan).limit(1)
        results = qry.execute()
        channel_data = {}
        for channel in results:
            channel_data = dict(channel)
        return channel_data

    def chan_list(metadata, session):
        rss_feeds = Table("rss_feeds", metadata, autoload=True)
        qry = rss_feeds.select().order_by(rss_feeds.c.feed_title.asc())
        results = qry.execute()
        channel_list = []
        for channel in results:
            channel_data = dict(channel)
            channel_list.append(channel_data)
        return channel_list

    def show_chans(metadata, session):
        channel_list = SVC_RSS.chan_list(metadata, session)
        text_data = "| "
        for channel in channel_list:
            chan_data = dict(channel)
            text_data += (
                chan_data["feed_title"] + " [" + str(chan_data["feed_id"]) + "]" + " | "
            )
        return text_data
