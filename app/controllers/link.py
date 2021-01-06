import re
import json
import datetime
import html2text
from loguru import logger
import requests
import bs4 as BeautifulSoup
import http
from .google import SVC_Google
from .twitter import SVC_Twitter
from sqlalchemy import Table, insert


from app import metadata, session


class SVC_Link:
    def cmd_link(code_or_url):
        # Check for a comma, and determine page count, unfinished...
        page_count = 3
        pos1 = str(code_or_url).find(",")
        if pos1 > 0:
            phrase = str(code_or_url)[:pos1]
            page_count = str(code_or_url)[pos1 + 1 :].strip()
            try:
                page_count = int(page_count)
                logger.warning("Page Count Specified: " + str(page_count))
            except:
                logger.warning("Error. Multilink Not Enabled")
                page_count = 3
        else:
            phrase = str(code_or_url)
        pos1 = phrase.find(".")
        if pos1 >= 0:
            logger.debug("Using URL")
            # Do URL Magic Here
            link_code = SVC_Google.proc_link(phrase, metadata, session)
            logger.debug("Link Code: " + link_code)
        else:
            logger.debug("Using Link Code")
            link_code = phrase
        # Link Code has been established by this point
        link_url = ""
        links = Table("links", metadata, autoload=True)
        qry = links.select().where(links.c.link_code == link_code)
        results = qry.execute()
        # headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:69.0) Gecko/20100101 Firefox/69.0"}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            # "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "If-None-Match": 'W/"2d948-yE4NiwNgR4dh3fmcnU5LR8bysMg"',
            "Cache-Control": "max-age=0",
        }
        text_data = ""
        rowcount = len(results._saved_cursor._result.rows)
        if rowcount == 0:
            logger.warning("Link Code " + link_code + " can not be found.")
            link_text = (
                "Link Code for: "
                + link_code
                + " can not be found. Please check the link and try again."
            )
        else:
            for x in results:
                link_row = list(x)
                link_url = link_row[2]
            logger.debug("Now fetching: " + link_code + " | " + link_url)
            file_ext_dot = link_url.rfind(".") + 1
            file_ext = link_url[file_ext_dot : file_ext_dot + 3]
            logger.debug("Filetype found: " + file_ext)
            if file_ext == "pdf":
                logger.debug("PDF Filetype Detected. Aborting.")
                link_text = (
                    "Apologies. You have requested a PDF file, which is not supported by your end. "
                    "We are working on a solution to allow the reading of PDF files, but this feature is not yet available"
                )
            else:
                try:
                    logger.debug("Getting URL: " + link_url)
                    r = requests.get(link_url, headers=headers, timeout=5)
                    r.raise_for_status()
                    link_text = r.text
                except requests.exceptions.HTTPError as errh:
                    link_text = "Http Error: " + str(errh)
                except requests.exceptions.ConnectionError as errc:
                    link_text = "Error Connecting: " + str(errc)
                except requests.exceptions.Timeout as errt:
                    link_text = "Timeout Error: " + str(errt)
                except requests.exceptions.RequestException as err:
                    link_text = "OOps: Something went wrong: " + str(err)
                except:
                    link_text = "OOps: Something went wrong: Unknown Error"
                if link_text[:3] == "%PDF":
                    link_text = (
                        "Apologies. You have requested a PDF file, which is not supported by your end. "
                        "We are working on a solution to allow the reading of PDF files, but this feature is not yet available"
                    )
        pos1 = link_url.find("amazon.com")
        pos2 = link_url.find("/dp/")
        pos3 = link_url.find("://twitter.com/")
        # Filter Link Returns
        if (pos1 >= 0) and (pos2 >= 0):
            logger.debug("Using Amazon Filter")
            # try to find asin to use api
            asin = link_url[pos2 + 4 :]
            pos1 = asin.find(r"/")
            asin = asin[:pos1]

            # ScrapeHero Code ----------------
            conn = http.client.HTTPSConnection("get.scrapehero.com")
            conn.request(
                "GET",
                "/amz/product-details/?x-api-key=SXOFpa27z4vriRCOlfQC7IZOdxYWo9Xj&asin="
                + asin
                + "&country_code=US",
            )
            res = conn.getresponse()
            data = res.read()
            json_data = json.loads(data.decode("utf-8"))
            prod_data = dict(json_data)
            show = ""
            end = "[EOL]" + chr(13) + chr(10)
            for k, v in prod_data.items():
                try:
                    show += k + ": " + v + end
                except:
                    pass
            amz_details = show
            # --------------------------

            body_text = SVC_Link.to_text(str(amz_details), rehtml=True)
        elif pos3 >= 0:
            logger.debug("Using Twitter Filter")
            body_text = SVC_Twitter.parse_twitter(link_url)
        else:
            logger.debug("Not Using Filters")
            body_text = "URL: " + link_url + "\r\n"
            body_text += (
                "Link Code: " + link_code + " \r\n" + SVC_Link.to_text(link_text)
            )
        return body_text, page_count

    def make_text_old(html_src):
        try:
            soup = BeautifulSoup.BeautifulSoup(html_src, "lxml")
            html_body = soup.body
            soup.script.decompose()
            selects = html_body.findAll("script")
            for match in selects:
                match.decompose()
            selects = html_body.findAll("CDATA")
            for match in selects:
                match.decompose()
            link_text = html_body.text
            i = 0
            while i < 100:
                link_text = link_text.replace("  ", " ")
                link_text = link_text.replace("  ", " ")
                link_text = link_text.replace("  ", " ")
                link_text = link_text.replace("\r\n\r\n", "\r\n")
                link_text = link_text.replace("\r\n\r\n", "\r\n")
                link_text = link_text.replace("\r\n\r\n", "\r\n")
                link_text = link_text.replace("\n\n", "\n")
                link_text = link_text.replace("\n\n", "\n")
                link_text = link_text.replace("\r\r", "\r")
                link_text = link_text.replace("\r\r", "\r")
                i += 1

            find_cdata = link_text.find("CDATA")
            if find_cdata > 0:
                cdata_exists = 1
            else:
                cdata_exists = 0
            i = 0
            while i < 10:
                pos1 = link_text.find("//<![CDATA[")
                pos2 = link_text.find("//]]>", pos1) + 5
                link_text = link_text[:pos1] + link_text[pos2:]
                find_cdata = link_text.find("CDATA")
                if find_cdata > 0:
                    cdata_exists = 1
                else:
                    cdata_exists = 0
                i += 1

        except requests.exceptions.HTTPError as err:
            link_text = str(err) + "\r\n"
            link_text += (
                "Apologies. This site could not be parsed into text for you. "
                "Sites with a lot of multi-media and Javascript pose a particular set of problems for "
                "our cutting-and-pasting robots, slave-labor, and interns. We will be improving the "
                "technology we use continuous, but unfortunatley you have requested a site we can not "
                "yet parse. Please save the link code, and try it again another time."
            )
        except:
            # link_text = str(err) + "\r\n"
            link_text = (
                "Apologies. This site could not be parsed into text for you. "
                "Sites with a lot of multi-media and Javascript pose a particular set of problems for "
                "our cutting-and-pasting robots, slave-labor, and interns. We will be improving the "
                "technology we use continuous, but unfortunatley you have requested a site we can not "
                "yet parse. Please save the link code, and try it again another time."
            )
        return link_text

    def make_text(html_src):
        soup = BeautifulSoup.BeautifulSoup(html_src, "lxml")
        [x.extract() for x in soup.findAll(["script", "style", "noscript", "a"])]
        soup = soup.get_text(strip=True)
        text_data = soup
        return text_data

    def to_text(html_src, rehtml=True):
        html_data = str(html_src)
        html_data = html_data.replace("\t", " ")
        while (html_data.find("  ")) >= 0:
            html_data = html_data.replace("  ", " ")
        while (html_data.find(chr(9))) >= 0:
            html_data = html_data.replace(chr(9), " ")
        parser = html2text.HTML2Text()
        parser.wrap_links = True
        parser.unicode_snob = True
        parser.skip_internal_links = True
        parser.inline_links = True
        parser.ignore_anchors = True
        parser.ignore_images = True
        parser.ignore_emphasis = True
        parser.ignore_links = True
        try:
            text = parser.handle(html_data)
        except Exception as e:
            logger.warning("HTML2Text Failed")
            logger.info(str(e))
            text = str(html_data)
        if rehtml:
            text = text.replace("\\", "")
        text = re.sub(r"â", r"'", text)
        text = re.sub(r"Â»", r">>", text)
        text = re.sub(r"’", "'", text)
        text = re.sub(r"‘", "'", text)
        text = re.sub(r"©", "(c)", text)
        text = SVC_Link.low_ascii(text)
        text = text.replace("\r", "[EOL]")
        text = text.replace("\n", "[EOL]")
        for x in range(0, 30):
            text = text.replace("[EOL]        [EOL]", "[EOL]")
            text = text.replace("[EOL]       [EOL]", "[EOL]")
            text = text.replace("[EOL]      [EOL]", "[EOL]")
            text = text.replace("[EOL]     [EOL]", "[EOL]")
            text = text.replace("[EOL]    [EOL]", "[EOL]")
            text = text.replace("[EOL]   [EOL]", "[EOL]")
            text = text.replace("[EOL]  [EOL]", "[EOL]")
            text = text.replace("[EOL] [EOL]", "[EOL]")
            text = text.replace("[EOL][EOL]", "[EOL]")
        text = text.replace("[EOL]", "\r\n")
        return text

    def low_ascii(in_text):
        text_data = str(in_text)
        new_str = ""
        for char in text_data:
            ascii_code = ord(char)
            if ascii_code > 126:
                new_str += "*"
            else:
                new_str += char
        return new_str

    def insert_outbound(
        reg_num, msg_in_id, node_id, subject, message, metadata, session
    ):
        stamp = datetime.datetime.now()
        msg_out = Table("msg_outbound", metadata, autoload=True)
        i = insert(msg_out)
        i = i.values(
            {
                "msg_in_id": msg_in_id,
                "node_id": node_id,
                "reg_num": reg_num,
                "subject": subject,
                "message": message,
                "cb_date": stamp,
            }
        )
        session.execute(i)

    def upd_out_msg(msg_out_id, subject, message, metadata, session):
        new_subject = subject
        new_message = message
        new_stamp = datetime.datetime.now()
        msg_outbound = Table("msg_outbound", metadata, autoload=True)
        upd = (
            msg_outbound.update()
            .values(subject=new_subject, message=new_message, cb_date=new_stamp)
            .where(msg_outbound.c.msg_out_id == msg_out_id)
        )
        session.execute(upd)
        session.commit()

    def filter_amazon(html_src):
        link_text = ""
        soup = BeautifulSoup.BeautifulSoup(html_src, "lxml")
        dp_container = soup.find("div", {"id": "dp-container"})
        if dp_container != None:
            link_text += SVC_Link.to_text(html_src, rehtml=True)
        else:
            link_text = soup.find("div", {"id": "centerCol"})
        return link_text
