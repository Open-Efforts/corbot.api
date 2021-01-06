import json
import datetime
import requests

from app import metadata, session

# import app.controllers.test  # noqa 401
# import app.controllers.runner  # noqa 401
from app.logger import log
from sqlalchemy import Table, MetaData
from imdb import IMDb
from loguru import logger
from .wiki import SVC_Wikipedia
from .link import SVC_Link
from .google import SVC_Google
from .lyrics import SVC_Lyrics
from .amazon import SVC_Amazon
from .info import SVC_Info
from .musicmap import SVC_MusicMap
from .news import SVC_News
from .rss import SVC_RSS
from .sports import SVC_Rundown
from .twitter import SVC_Twitter
from .account import SVC_Account
from .runner import Runner
from .cb import CB
from .comm import comm


def cmd_weather(arg):
    api_key = "613fb6ff84bb0b3c7ede9da0b950aabd"
    zip_code = arg
    r_str = "http://api.openweathermap.org/data/2.5/"
    r_str += "forecast?zip=" + zip_code
    r_str += "&APPID=" + api_key
    r_str += "&units=imperial"
    r = requests.get(r_str)
    # print(r_str)
    w_data = r.json()
    # print(w_data)
    try:
        city = w_data["city"]
        msg_txt = "Weather for: " + city["name"] + "\r\n"
        cnt = 0
        for x in w_data["list"]:
            row = dict(x)
            row_main = row["main"]
            row_weather = row["weather"][0]
            weather = row_weather["description"]
            row_wind = row["wind"]
            row_wind = row_wind["speed"]
            show_temp_min = str(int(row_main["temp_min"]))
            show_temp_max = str(int(row_main["temp_max"]))
            show_humidity = str(row_main["humidity"])
            show_wind = " / Wind " + str(row_wind) + " Mph"
            show = (
                ": "
                + weather
                + " / Min "
                + show_temp_min
                + " F / Max "
                + show_temp_max
                + " F / Humidity "
                + show_humidity
                + "%"
                + show_wind
            )
            new_day = datetime.datetime.today() + datetime.timedelta(days=cnt)
            new_day = new_day.strftime("%A %b %d")
            show_row = new_day + show + "\r\n"
            msg_txt += show_row
            cnt += 1
            if cnt == 5:
                break
    except:
        msg_txt = "city not found"
    return msg_txt


def cmd_stocks(phrase):
    # https://iextrading.com/apps/stocks/
    symbol = str(phrase)
    the_symbol = symbol.strip().lower()
    token_public = "pk_7aa0b4775705405991286508480ffca0"
    token_secret = "sk_3b1c5752708c4f569c4fb4158b907f5e"
    try:
        body_text = "Your Stock Quote for: [EOL]"
        url = (
            "https://cloud.iexapis.com/stable/tops?token="
            + token_public
            + "&symbols="
            + symbol
        )
        r = requests.get(url)
        j_data = r.json()
        d_data = j_data[0]
        for k, v in d_data.items():
            if k == "lastUpdated":
                unixtime = str(v)
                unixtime = unixtime[:10]
                unixtime = int(unixtime)
                lastUpdated = datetime.datetime.fromtimestamp(unixtime).strftime(
                    "%Y-%m-%d %H:%M"
                )
                body_text += str(k) + ": " + str(lastUpdated) + "[EOL]"
            elif k == "lastSaleTime":
                unixtime = str(v)
                unixtime = unixtime[:10]
                unixtime = int(unixtime)
                lastSaleTime = datetime.datetime.fromtimestamp(unixtime).strftime(
                    "%Y-%m-%d %H:%M"
                )
                body_text += str(k) + ": " + str(lastSaleTime) + "[EOL]"
            else:
                body_text += str(k) + ": " + str(v) + "[EOL]"
        body_text += "------------------------------------[EOL]"
        body_text += "Company Data" + "[EOL]"
        url = (
            "https://cloud.iexapis.com/stable/stock/"
            + symbol
            + "/company?token="
            + token_public
        )
        r = requests.get(url)
        j_data = r.json()
        d_data = j_data
        for k, v in d_data.items():
            body_text += str(k) + ": " + str(v) + "[EOL]"
    except:
        body_text = (
            "Apologies. Something went wrong. Please check the Stock Symbol and try again, or send a request"
            " with Info in the subject line, and Stocks in the body of the message for detailed instructions"
            " on how to use the Stocks service."
        )
    # body_text = SVC_Link.to_text(body_text,rehtml=True)
    # body_text = body_text.encode('ascii', 'replace').decode()
    return body_text


def cmd_crypto(phrase):
    db_ip = "104.248.212.184"
    db_name = "coinstack"
    db_user = "corbot_admin"
    db_pass = "4uYwZTiMaZ2w3Zbnqr"
    engine_str = (
        "mysql+pymysql://" + db_user + ":" + db_pass + "@" + db_ip + "/" + db_name
    )
    engine2 = create_engine(
        engine_str, pool_size=10, max_overflow=10, pool_recycle=3600
    )
    # Settings
    conn2 = engine2.connect()
    metadata2 = MetaData(bind=engine2)
    body_text = "Latest Crypto Currency Pricing (USD):[EOL]"
    pricing = Table("pricing", metadata2, autoload=True)
    qry = pricing.select().limit(1).order_by(pricing.c.unix_time.desc())
    results = qry.execute()
    # Needs to be re-done with Pandas to prevent the needless 2x queries
    for row in results:
        plan_row = dict(row)
        body_text += "Last Updated: " + str(plan_row["stamp"]) + "[EOL]"
        body_text += "Bitcoin [BTC]: " + str(plan_row["btc"]) + "[EOL]"
        body_text += "Ethereum [ETH]: " + str(plan_row["eth"]) + "[EOL]"
        body_text += "Ripple [XRP]: " + str(plan_row["xrp"]) + "[EOL]"
        body_text += "Bitcoin Cash [BCH]: " + str(plan_row["bch"]) + "[EOL]"
        body_text += "Litecoin [LTC]: " + str(plan_row["ltc"]) + "[EOL]"
        body_text += "Monero [XMR]: " + str(plan_row["xmr"]) + "[EOL]"
        body_text += "[EOL]"
    history = Table("history", metadata2, autoload=True)
    qry = history.select().limit(10).order_by(history.c.day.desc())
    results = qry.execute()
    body_text += "----------------Bitcoin 10 Day ------------------[EOL]"
    body_text += "---Date----|--BTC lw---|--BTC hi---|--BTC av--[EOL]"
    for row in results:
        btc_lw = str(round(row["btc_lw"], 4))
        btc_lw = btc_lw.ljust(9, "0")
        btc_hi = str(round(row["btc_hi"], 4))
        btc_hi = btc_hi.ljust(9, "0")
        btc_av = str(round(row["btc_av"], 4))
        btc_av = btc_av.ljust(9, "0")
        body_text += (
            str(row["day"]) + " | " + btc_lw + " | " + btc_hi + " | " + btc_av + "[EOL]"
        )
    body_text += "----------------Ethereum 10 Day ------------------[EOL]"
    body_text += "---Date----|--ETH lw---|--ETH hi---|--ETH av--[EOL]"
    history = Table("history", metadata2, autoload=True)
    qry = history.select().limit(10).order_by(history.c.day.desc())
    results = qry.execute()
    for row in results:
        eth_lw = str(round(row["eth_lw"], 4))
        eth_lw = eth_lw.ljust(9, "0")
        eth_hi = str(round(row["eth_hi"], 4))
        eth_hi = eth_hi.ljust(9, "0")
        eth_av = str(round(row["eth_av"], 4))
        eth_av = eth_av.ljust(9, "0")
        body_text += (
            str(row["day"]) + " | " + eth_lw + " | " + eth_hi + " | " + eth_av + "[EOL]"
        )
    return body_text


def cmd_imdb(arg):
    movie_request = arg
    comma_check = movie_request.find(",")
    if comma_check < 1:
        movie_request = "Movie, " + movie_request
    movie_request = movie_request.lower()
    movie_request = movie_request.replace("(", "")
    movie_request = movie_request.replace(")", "")
    movie_request = movie_request.split(",", 1)
    movie_request[0] = movie_request[0].rstrip("s")
    movie_request[1] = movie_request[1].lstrip()
    logger.debug(movie_request)
    ia = IMDb()
    text_data = ""
    if (
        (len(movie_request[1]) == 7)
        and (movie_request[1].isdigit())
        and (movie_request[0] == "movie")
    ):
        get_movie = ia.get_movie(movie_request[1])
        # We get an error here when the IMDB data is incomplete
        try:
            plot = str(get_movie["plot"])
            plot1 = plot.rfind("::")
            plot = plot[2:plot1]
            text_data = (
                (
                    "Title: "
                    + str(get_movie["title"])
                    + " Year:"
                    + str(get_movie["year"])
                )
                + "\r\n"
                + "\r\n"
            )
            text_data += ("Plot: " + plot) + "\r\n" + "\r\n"
        except:
            text_data += "Plot: Unavailable" + "\r\n"
        try:
            actors_src = str(get_movie["actors"])
            actors_src = actors_src.replace("[http] ", "', '")
            actors_src = actors_src.replace("<", "'")
            actors_src = actors_src.replace(":", "':'")
            actors_src = actors_src.replace(">", "'")
            actors_src = actors_src.replace("[", "")
            actors_src = actors_src.replace("]", "")
            actors_src = actors_src.replace("_", " ")
            actors_src = actors_src.replace("'Person id", "*'[")
            actors_src = actors_src.replace("name", "]")
            # actor_src = actors_src.replace(',', " ")
            actors_src = actors_src.split("*")
            actors = ""
            # print(actors_src)
            for x in actors_src[0:20]:
                actor_row = x.replace("'", "")
                actor_row = actor_row.replace("[:", "[")
                actor_row = actor_row.replace(", ]", "]")
                actor_row = actor_row.rstrip()
                actor_row = actor_row[10:] + actor_row[0:9] + " | "
                actor_row = actor_row.replace(",[", "[")
                actors += actor_row
            text_data += (
                "To look up one of these actors, just send back a message with the subject: imdb:"
                + "\r\n"
            )
            text_data += "In the body type:      movie, Actor_ID    example:" + "\r\n"
            text_data += "actor, 0073195" + "\r\n" * 2
            text_data += actors
        except Exception as E:
            text_data += "Actor Data: Unavailable"

    elif (
        (len(movie_request[1]) == 7)
        and (movie_request[1].isdigit())
        and (movie_request[0] == "actor")
    ):
        try:
            get_actor = ia.get_person(movie_request[1])
            first_name = str(get_actor["filmography"])
            first_name = first_name.replace("[http] ", "', '")
            first_name = first_name.replace("<", "'")
            first_name = first_name.replace(":", "':'")
            first_name = first_name.replace(">", "'")
            first_name = first_name.replace("[", "")
            first_name = first_name.replace("]", "")
            first_name = first_name.replace("_", " ")
            first_name = first_name.replace("'Movie id", "*'(")
            first_name = first_name.replace("title", ")")
            first_name = first_name.split("*")
            movies = ""
            for x in first_name[1:]:
                movie_row = x.replace("'", "")
                movie_row = movie_row.replace("(:", "")
                movie_row = movie_row.replace("):", "")
                movie_row = movie_row.replace(") ,", ")")
                movies += movie_row[10:] + "[" + movie_row[0:7] + "]" + " | "
            text_data = "Films this actor was in: " + "\r\n" + movies
            text_data += (
                "\r\n" * 2
                + "To look up these movies, just send back a message with the subject: imdb:"
                + "\r\n"
            )
            text_data += "In the body type:      movie, Movie_ID     example:" + "\r\n"
            text_data += "movie, 0073195"
        except:
            text_data = "This number is invalid, please check the number."

    elif movie_request[0] == "actor":
        try:
            s_result = ia.search_person(movie_request[1])
            actor_list = str(s_result)
            actor_list = actor_list.replace("[http] ", "', '")
            actor_list = actor_list.replace("<", "'")
            actor_list = actor_list.replace(":", "':'")
            actor_list = actor_list.replace(">", "'")
            actor_list = actor_list.replace("[", "")
            actor_list = actor_list.replace("]", "")
            actor_list = actor_list.replace("_", " ")
            actor_list = actor_list.replace("'Person id'", "*'[")
            actor_list = actor_list.replace("title", "")
            actor_list = actor_list.split("*")
            actors = ""

            for x in actor_list:
                actor_row = x.replace("'", "")
                actor_row = actor_row.replace("[:", "[")
                actor_row = actor_row.replace(", ]", "]")
                actor_row = actor_row.rstrip()
                actor_row = actor_row[15:] + actor_row[0:9] + ")" + " | "
                actor_row = actor_row.replace(",[", "[")
                actor_row = actor_row.replace(",)", "]")
                actor_row = actor_row.replace(") |", "")
                actors += actor_row
            movie_search = []
            for item in s_result:
                movie_search.append(item.personID)
            first_result = ia.get_person(movie_search[0])
            first_name = str(first_result["filmography"])
            first_name = first_name.replace("[http] ", "', '")
            first_name = first_name.replace("<", "'")
            first_name = first_name.replace(":", "':'")
            first_name = first_name.replace(">", "'")
            first_name = first_name.replace("[", "")
            first_name = first_name.replace("]", "")
            first_name = first_name.replace("_", " ")
            first_name = first_name.replace("'Movie id", "*'[")
            first_name = first_name.replace("title", "]")
            first_name = first_name.split("*")
            movies = ""
            for x in first_name[1:]:
                movie_row = x.replace("'", "")
                movie_row = movie_row.replace("[:", "")
                movie_row = movie_row.replace("]:", "")
                movie_row = movie_row.replace(",)", "]")
                movie_row = movie_row[10:] + "[" + movie_row[0:7] + "]" + " | "
                movie_row = movie_row.replace("[]", "")
                movies += movie_row.replace(") , [", ") [")
            text_data += (
                "Here are the films that " + str(first_result) + " was in:" + "\r\n"
            )
            text_data += (
                "To look up these movies, just send back a message with the subject: imdb:"
                + "\r\n"
            )
            text_data += "In the body type:      movie, Movie_ID     example:" + "\r\n"
            text_data += "movie, 0073195" + "\r\n" * 2
            text_data += movies
            text_data += (
                "\r\n" + "\r\n" + "Here are other names that came up: " + "\r\n"
            )
            text_data += (
                "To look up one of these actors, just send back a message with the subject: imdb:"
                + "\r\n"
            )
            text_data += "In the body type:      movie, Actor_ID    example:" + "\r\n"
            text_data += "actor, 0073195" + "\r\n" * 2
            text_data += actors
        except:
            logger.info("No actor by this name, please check the spelling.")
    #######################

    elif movie_request[0] == "movie":
        try:
            s_result = ia.search_movie(movie_request[1])
            movie_list = str(s_result)
            # format movie list
            movie_list = movie_list.replace("[http] ", "', '")
            movie_list = movie_list.replace("<", "'")
            movie_list = movie_list.replace(":", "':'")
            movie_list = movie_list.replace(">", "'")
            movie_list = movie_list.replace("[", "")
            movie_list = movie_list.replace("]", "")
            movie_list = movie_list.replace("_", " ")
            movie_list = movie_list.replace("'Movie id", "*'[")
            movie_list = movie_list.replace("title", "]")
            movie_list = movie_list.split("*")
            movies = ""
            for x in movie_list:
                movie_row = x.replace("'", "")
                movie_row = movie_row.replace("[:", "")
                movie_row = movie_row.replace("]:", "")
                movie_row = movie_row.replace(",)", "]")
                movie_row = movie_row[10:] + "[" + movie_row[0:7] + "]" + " | "
                movie_row = movie_row.replace("[] ", "")
                movies += movie_row.replace(") , [", ") [")

            movie_search = []

            for item in s_result:
                # text_data = str((item['long imdb canonical title'], item.movieID))
                movie_search.append(item.movieID)
            first_result = ia.get_movie(movie_search[0])
            logger.debug(first_result)
            title = str(first_result["title"])
            year = str(first_result["year"])
            plot = str(first_result["plot"])
            plot1 = plot.rfind("::")
            plot = plot[2:plot1]
            actors_src = str(first_result["actors"])

            # print(actors_src,'\r\n')
            actors_src = actors_src.replace("[http] ", "', '")
            actors_src = actors_src.replace("<", "'")
            actors_src = actors_src.replace(":", "':'")
            actors_src = actors_src.replace(">", "'")
            actors_src = actors_src.replace("[", "")
            actors_src = actors_src.replace("]", "")
            actors_src = actors_src.replace("_", " ")
            actors_src = actors_src.replace("'Person id", "*'[")
            actors_src = actors_src.replace("name", "]")
            # actor_src = actors_src.replace(',', " ")
            actors_src = actors_src.split("*")
            actors = ""
            # print(actors_src)
            for x in actors_src[0:20]:
                actor_row = x.replace("'", "")
                actor_row = actor_row.replace("[:", "[")
                actor_row = actor_row.replace(", ]", "]")
                actor_row = actor_row.rstrip()
                actor_row = actor_row[10:] + actor_row[0:9] + " | "
                actor_row = actor_row.replace(",[", "[")
                actors += actor_row
            text_data += "Title: " + title + " (" + year + ")\r\n"
            text_data += "Plot: " + plot + "\r\n" + "\r\n"
            text_data += (
                "To look up one of these actors, just send back a message with the subject: imdb:"
                + "\r\n"
            )
            text_data += "In the body type:      movie, Actor_ID    example:" + "\r\n"
            text_data += "actor, 0073195" + "\r\n" + "\r\n"
            text_data += "Actors: " + actors + "\r\n" + "\r\n"
            text_data += (
                "To look up these other movies, just send back a message with the subject: imdb:"
                + "\r\n"
            )
            text_data += "In the body type:      movie, Movie_ID     example:" + "\r\n"
            text_data += "movie, 0073195" + "\r\n" + "\r\n"
            text_data += movies
        except:
            logger.info("No movie by this name, please check the spelling.")

    return text_data


MAP = {
    "weather": cmd_weather,
    "stock": cmd_stocks,
    "crypto": cmd_crypto,
    "imdb": cmd_imdb,
    "wikipedia": SVC_Wikipedia.cmd_wiki,
    "link": SVC_Link.cmd_link,
    "news": SVC_News.cmd_news,
    "google": SVC_Google.cmd_google,
    "twitter": SVC_Twitter.cmd_twitter,
    "sports": SVC_Rundown.cmd_odds,
    "scores": SVC_Rundown.cmd_scores,
    "rss": SVC_RSS.cmd_rss,
    "musicmap": SVC_MusicMap.cmd_musicmap,
    "info": SVC_Info.cmd_info,
    "amazon": SVC_Amazon.cmd_amazon,
    "lyrics": SVC_Lyrics.cmd_lyrics,
    "account": SVC_Account.cmd_account,
}

human_svcs = set(["support", "billing", "alfred", "error"])
comm_svc = set(["sms", "email"])


def dispatch(method_name: str, body: str, reg_num: str):
    log(log.DEBUG, "dispatch()")
    log(log.DEBUG, "method name: %s", method_name)
    log(log.DEBUG, "body: %s", body)
    log(log.DEBUG, "reg_num: %s", reg_num)
    method_name = method_name.lower()
    method_name_ident = Runner.service_ident(method_name).lower()
    if method_name_ident in MAP:
        method = MAP[method_name_ident]
        try:
            if method_name_ident == "account":
                subject, data = method(reg_num)
                return dict(
                    request=method_name_ident,
                    data=data.replace("\r\r", "\n\n").replace("\r", "\n"),
                    indent=4,
                    sort_keys=True,
                    default=str,
                )
            else:
                return dict(
                    request=method_name_ident,
                    data=method(body).replace("\r\n", "\n"),
                    indent=4,
                    sort_keys=True,
                    default=str,
                )
        except Exception as e:
            log(log.ERROR, e)
            raise e
        # data = json.dumps(method(body))
        # data = [ i.split('|') for i in method(body).split('\r\n')]
        # return dict(request=method_name, data=data)
    else:
        client_id = Runner.get_client_id(reg_num)
        if method_name in human_svcs:
            return dict(
                client_id=client_id, svc_feature="human", expired=comm(client_id)
            )
        contact_name = CB.unparse_contact_name(method_name)
        if contact_name:
            found, contact_data = CB.check_contact(client_id, contact_name)
            if found == 1:
                if contact_data["contact_type"] == "number":
                    svc_feature = "sms"
                else:
                    svc_feature = contact_data["contact_type"]
                return dict(
                    client_id=client_id,
                    svc_feature=svc_feature,
                    expired=comm(client_id),
                )
            else:
                return dict(
                    client_id=client_id,
                    svc_feature="No such contact for this user",
                    expired=comm(client_id),
                )
        elif "@" in method_name:
            return dict(
                client_id=client_id, svc_feature="email", expired=comm(client_id)
            )
        elif method_name.isdigit():
            return dict(client_id=client_id, svc_feature="sms", expired=comm(client_id))
        else:
            raise NameError("Such service is not supported")
