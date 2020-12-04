import json
import urllib
from loguru import logger
import requests
from sqlalchemy import *

from app import metadata, session


def cmd_google(phrase):
    q = str(phrase)
    # Temporarily taking out quote until more testing can be done not on a fucking friday
    q = q.replace('"', "")
    q = q.replace("/", " ")
    q = q.replace(".", " ")
    q = urllib.parse.quote(q)
    # q = urllib.parse.quote_plus(q)
    # logger.debug(q)
    # key = 'AIzaSyDjMNvFbRptnZUt55zeh4MMukUS69aGrhI'
    key = "AIzaSyBI3MiiEXEKNyPPfoCnGSq8W9TpSedhHeY"
    cx = "001690443504898094366:n-vrnapnina"
    # cx = 'cb-api-1550765294709'
    base_url = "https://www.googleapis.com/customsearch/v1"
    new_url = base_url + "?key=" + key + "&cx=" + cx + "&q=" + q
    ret_data = ""
    # logger.debug(new_url)
    r = requests.get(new_url)
    json_data = r.text
    j = json.loads(json_data)
    # logger.debug(j)
    try:
        error_found = j["error"]
        logger.warning(error_found)
        ret_data = (
            "We are experiencing technical difficulties with our Google search feature at the moment. Please try your search again later for "
            + str(phrase)
        )
    except:
        try:
            items = j["items"]
            cnt = 1
            for x in items:
                row = x
                res_cnt = "(# " + str(cnt) + ") "
                res_title = row["title"]
                res_snippet = row["snippet"]
                res_link = "Link: " + row["link"]
                # ret_data += res_cnt + " " + res_title + "\r\n"
                ret_data += res_title + "\r\n"
                ret_data += res_link + "\r\n"
                try:
                    ret_data += (
                        "Link Code: "
                        + proc_link(row["link"], metadata, session)
                        + "\r\n"
                    )
                except:
                    ret_data += "Link Code: " + "[unavailable]" + "\r\n"
                    logger.warning(
                        "Could Not B36 Encode link: " + row["link"])
                ret_data += res_snippet + "\r\n"
                ret_data += "\r\n"
                cnt += 1
        except:
            ret_data = "No Google search results found. Please check your spelling and try again."
    data = ret_data
    return data


def proc_link(link_url):
    # Find URL in DB
    the_url = str(link_url)
    status = link_exists(the_url, metadata)
    if status[0] == True:
        # logger.debug("Link Exists, pulling the existing link_code")
        link_code = status[1]
    else:
        # logger.debug("Link Does Not Exists, entering the link into the DB and recovering the code")
        safe_link = str(link_url)
        safe_link = safe_link[:511]
        links = Table("links", metadata, autoload=True)
        i = insert(links)
        i = i.values({"link_url": safe_link})
        session.execute(i)
        session.commit()
        link_codes(metadata, session)
        status = link_exists(link_url, metadata)
        link_code = status[1]
    return link_code


def link_codes():
    links = Table("links", metadata, autoload=True)
    qry = links.select().where(links.c.link_code == None)
    res = qry.execute()
    rowcount = len(res._saved_cursor._result.rows)
    link_rows = {}
    cnt = 0
    for row in res:
        link_rows[cnt] = dict(row)
        link_row = link_rows[cnt]
        # logger.debug(link_rows[cnt])
        cnt += 1
        link_id = link_row["link_id"]
        link_code = int_to_base36(link_id)
        # Got B36 Encoding, update link_code
        links = Table("links", metadata, autoload=True)
        upd = (
            links.update()
            .values(link_code=link_code)
            .where(links.c.link_id == link_id)
        )
        session.execute(upd)
        session.commit()


def link_exists(link_url):
    links = Table("links", metadata, autoload=True)
    qry = links.select().where(links.c.link_url == link_url).limit(1)
    results = qry.execute()
    rowcount = len(results._saved_cursor._result.rows)
    if rowcount > 0:
        found = True
        for x in results:
            link_code = x[1]
    else:
        found = False
        link_code = ""
    return found, link_code


def int_to_base36(num):
    """Converts a positive integer into a base36 string."""
    assert num >= 0
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    res = ""
    while not res or num > 0:
        num, i = divmod(num, 36)
        res = digits[i] + res
    return res
