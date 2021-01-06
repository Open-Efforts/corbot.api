import re
import json
import requests
import http
from .google import SVC_Google
import bs4 as BeautifulSoup
from sqlalchemy import Table


from app import metadata, session


class SVC_Amazon:
    def cmd_amazon(phrase):
        try:
            key_phrase = phrase.replace(" ", "+")
            conn = http.client.HTTPSConnection("get.scrapehero.com")
            conn.request(
                "GET",
                "/amz/keyword-search/?x-api-key=SXOFpa27z4vriRCOlfQC7IZOdxYWo9Xj&keyword="
                + key_phrase
                + "&country_code=US",
            )
            res = conn.getresponse()
            data = res.read()
            json_data = json.loads(data.decode("utf-8"))
            query = json_data["query"]
            results = json_data["search_results"]
            end = chr(13) + chr(10)
            show = str(query) + end
            for row in results:
                prod_data = dict(row)
                show += "Title: " + prod_data["name"] + end
                try:
                    show += "Sale Price: " + prod_data["sale_price"] + end
                except:
                    pass
                try:
                    show += "Regular Price: " + prod_data["regular_price"] + end
                except:
                    pass
                show += "ASIN: " + prod_data["asin"] + end
                try:
                    show += "Reviews: " + prod_data["review_count"] + end
                except:
                    pass
                try:
                    show += "Rating: " + prod_data["rating"] + end
                except:
                    pass

                try:
                    link_code = SVC_Google.proc_link(
                        prod_data["product_url"], metadata, session
                    )
                    show += "Link: " + link_code + end
                    show += ".................................." + end
                except:
                    pass
            text_out = show
        except Exception as E:
            end = chr(13) + chr(10)
            text_out = (
                "Error: There are No Amazon Search Results for the Request Phrase: "
                + end
            )
            text_out += "Request Phrase: " + phrase + end
            text_out += (
                "If you are sure of the spelling, please try your request again, if it fails again, please contact support."
                + phrase
                + end
            )
        return text_out

    def search_str(phrase):
        phrase_txt = str(phrase)
        fixed_phrase = phrase_txt.encode("ascii", errors="ignore").decode("ascii")
        fixed_phrase = phrase_txt.replace(" ", "+")
        return fixed_phrase

    def clean_text(in_text):
        text = str(in_text)
        fixed_text = ""
        fixed_text = fixed_text.replace("$", " $")
        fixed_text = " ".join(text.split())
        fixed_text = fixed_text.replace("$", " $")
        fixed_text = fixed_text.replace(
            "These are ads for products you'll find on Amazon.com.", ""
        )
        fixed_text = fixed_text.replace(
            "Clicking an ad will take you to the product's page.", ""
        )
        fixed_text = fixed_text.replace("Learn more about Sponsored Products.", "")
        fixed_text = fixed_text.replace("Sponsored", "")
        return fixed_text

    def get_amazon(url):
        debug_0 = False

        amz_page_data = {"best_programmer": "jeff"}
        get_page = requests.get(
            url,
            headers={
                "USER-AGENT": "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36",
                "ACCEPT": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "ACCEPT - ENCODING": "gzip, deflate, br",
                "ACCEPT-LANGUAGE": "n-US,en;q=0.5",
                "HOST": "www.amazon.com",
                "REFERER": "https://duckduckgo.com/",
                "TE": "trailers",
                "UPGRADE-INSECURE-REQUESTS": "1",
            },
        )
        page_data = get_page.text.encode("utf-8").strip()
        # page_data = page_data

        soup = BeautifulSoup.BeautifulSoup(page_data, "lxml")
        body = soup.find("body")
        # print(body.prettify)
        # dim
        error_code = ""
        text_data = ""

        # load byline / author
        try:
            temp_data = body.find(id="bylineInfo").text
            temp_data = SVC_Amazon.strip_spaces(temp_data)
            temp_data = SVC_Amazon.strip_code(temp_data)
            if debug_0 == True:
                print("byline temp_data --- " + temp_data)
            # get author
            startpos = temp_data.find("(Author)")
            if startpos > 0:
                book_author = temp_data[4:startpos]
                book_author = SVC_Amazon.strip_tail(book_author)
                amz_page_data["book_author"] = book_author
                if debug_0 == True:
                    print("author: " + book_author)
            else:
                if debug_0 == True:
                    print("author not found")
                amz_page_data["book_author"] = "Not found"
            # get byline
            try:
                temp_data = SVC_Amazon.strip_code(temp_data)
                # amz_page_data["byline_info"] = temp_data
                if debug_0 == True:
                    print("byline inserted - " + temp_data)
            except:
                if debug_0 == True:
                    print("byline insert failed - " + temp_data)
        except:
            amz_page_data["byline_info"] = "Not found"
            if debug_0 == True:
                print("byline not found: " + temp_data)

        # load book edition
        try:
            temp_data = body.find(id="bookEdition").text
            temp_data = SVC_Amazon.strip_tail(temp_data[0:])
            try:
                amz_page_data["book_edition"] = temp_data.strip()
                if debug_0 == True:
                    print("book edition inserted - " + temp_data)
            except:
                if debug_0 == True:
                    print("book edition insert failed - " + temp_data)
        except:
            amz_page_data["book_edition"] = "None listed"
            if debug_0 == True:
                print("book edition not found - " + temp_data)

        # title
        try:
            startpos = 0
            endpos = 0
            try:
                temp_data = body.find(id="booksTitle").text
                # print("1temp - " + temp_data)
                # print("1temp - " )
            except:
                # print("1fail")
                try:
                    temp_data = body.find("span", attrs={"id": "productTitle"})
                    # print("2temp - " + temp_data)
                    # print("2temp - " )
                except:
                    # print("2fail")
                    try:
                        temp_data = body.find("h1", attrs={"id": "title"}).text
                        # print("3temp")
                        # print("3temp " + temp_data)
                    except:
                        error_code = error_code + " title /"
                        print("1&2&3 title fail")
                        pass

            temp_data = SVC_Amazon.strip_spaces(temp_data)
            # print("strip spaces - " + temp_data)
            temp_data = SVC_Amazon.strip_code(temp_data)
            # print("strip code - " + temp_data)

            # cut after by .... (Author)
            try:
                endpos = temp_data.find("(Author)")
                # print("endpos found author - " + str(endpos) + " len " + str(len(temp_data)))
            except:
                # print("noendpos")
                endpos = 0

            if endpos > 0:
                # check for "by" as first word
                if temp_data.find("by") == 0:
                    # print("endpod0  " + str(endpos))
                    temp_data = temp_data[endpos + 9 :]
                    temp_data = SVC_Amazon.strip_head(temp_data)
                    # print(temp_data)
                # check for "by" after first word
                elif temp_data.find("by") > 0:
                    # loop to find "by" closest to author
                    # print("starting loop")

                    for startpos in range(0, endpos, 1):
                        if temp_data.find("by", startpos, len(temp_data)) > 0:
                            # print("startpos " + str(startpos))
                            # print("start data " + temp_data[startpos:endpos])
                            pass
                        else:
                            break
                    # loop to find the furthest author
                    for endpos in range(0, len(temp_data), 1):
                        if temp_data.find("Author", endpos, len(temp_data)) > 0:
                            # print("endpos " + str(endpos))
                            # print("end data " + temp_data[endpos:])
                            pass
                        else:
                            break
                    if startpos > 0:
                        startpos = startpos - 1
                    endpos = endpos + 6
                    # print(str(startpos) + " " + str(endpos))
                    # print(str(len(temp_data)))
                    left_data = temp_data[0:startpos]
                    # right_data = temp_data[endpos:len(temp_data)]
                    right_data = temp_data[endpos:]

                    temp_data = left_data + right_data
                    # print("left " + left_data)
                    # print("right " +right_data)
                else:
                    temp_data = temp_data[0:startpos]
            # cut Kindle edition
            startpos = temp_data.find("Kindle")
            if startpos > 0:
                temp_data = temp_data[0:startpos]
            # cut Paperback edition
            startpos = temp_data.find("Paperback")
            if startpos > 0:
                temp_data = temp_data[0:startpos]
            # cut Hardback edition
            startpos = temp_data.find("Hardback")
            if startpos > 0:
                temp_data = temp_data[0:startpos]
            # cut Hardcover edition
            startpos = temp_data.find("Hardcover")
            if startpos > 0:
                temp_data = temp_data[0:startpos]
            # cut Audio edition
            startpos = temp_data.find("Audiobook")
            if startpos > 0:
                temp_data = temp_data[0:startpos]
            # trim trailing end
            temp_data = SVC_Amazon.strip_tail(temp_data)
            # trim edition
            if temp_data[-7:] == "Edition":
                for lp in range(len(temp_data) - 9, 0, -1):
                    if temp_data[lp] == " ":
                        endpos = lp
                        break
                temp_data = temp_data[0:endpos]
            try:
                amz_page_data["book_title"] = temp_data
                if debug_0 == True:
                    print("book title inserted - " + temp_data)
            except:
                if debug_0 == True:
                    print("book title insert failed - " + temp_data)
                pass
        except:
            amz_page_data["book_title"] = "Error"
            error_code = error_code + " title /"
            print("book title error - " + str(temp_data))

        # description is a ul
        try:
            div_content = body.find("div", attrs={"class": "content"})
            # print("detail div " + div_content.prettify())
            # print("dv")
            try:
                li_items = div_content.find_all(
                    "li", attrs={"id": "", "class": "", "style": ""}
                )
                prod_details = {}
                try:
                    for item in li_items:
                        item_text = SVC_Amazon.strip_spaces(item.text)
                        item_key, item_value = item_text.split(":")
                        prod_details[item_key] = item_value
                    try:
                        amz_page_data["product_details_dict"] = str(prod_details)
                        if debug_0 == True:
                            print("product details inserted" + str(prod_details))
                    except:
                        if debug_0 == True:
                            print("product details insert failed" + str(prod_details))
                except:
                    amz_page_data["product_details_dict"] = "No details available"
                    if debug_0 == True:
                        print("product details not available")
            except:
                pass
        except:
            pass

        # Book types ------------------
        try:
            count = 0
            tab1 = False
            tab2 = False
            book_categories = {}
            book_details = {}

            # check for tab type
            try:
                # tab type 1
                div_content = body.find("div", attrs={"id": "MediaMatrix"})
                # print("div_content" + div_content.prettify())
                ul_content = div_content.find(
                    "ul",
                    attrs={
                        "class": re.compile(
                            "a-unordered-list a-nostyle a-button-list a-horizontal*"
                        )
                    },
                )
                # print("ul content 1" + ul_content.prettify())
                li_items = ul_content.find(
                    "li", attrs={"class": re.compile("swatchElement*")}
                )
                # print("li items 1")
                tab1 = True
                # print("tab1 " + str(tab1))
                # print("Tab1 " + str(li_items.prettify()))
            except:
                tab1 = False
                # print("tab1 " + str(tab1))

            try:
                # tab type 2
                div_content = body.find(
                    "div", attrs={"id": "mediaTabsGroup", "class": "feature"}
                )
                # print("div content " + div_content.prettify())
                ul_content = div_content.find("ul", attrs={"id": "mediaTabs_tabSet"})
                # print("ul content " + ul_content.prettify())
                tab2 = True
                # print("tab2 " + str(tab2))
                # print("tab2 " + str(ul_content.prettify()))
            except:
                tab2 = False
                print("tab2 " + str(tab2))

            # tab 1
            if tab1 == True:
                div_content = body.find("div", attrs={"id": "MediaMatrix"})
                # print("div_content 1" + div_content.prettify())
                ul_content = div_content.find(
                    "ul",
                    attrs={
                        "class": re.compile(
                            "a-unordered-list a-nostyle a-button-list a-horizontal*"
                        )
                    },
                )
                # print("ul 1 " + ul_content.prettify())
                try:
                    li_items = ul_content.find_all(
                        "li", attrs={"class": re.compile("swatchElement*")}
                    )
                    # print(li_items.prettify())
                    try:
                        # print("li for each")
                        for item in li_items:
                            # print(item.prettify())
                            book_type = ""
                            book_price = ""
                            book_price_alt = ""
                            count = count + 1
                            # type of book
                            try:
                                ele = item.find("a", attrs={"class": "a-button-text"})
                                book_type = ele.span.text
                                if book_type.find("Audiobook") > 0:
                                    book_type = "Audiobook"
                            except:
                                pass
                            # price
                            try:
                                ele = item.find("span", attrs={"class": "a-color-base"})
                                # print("price1 ele: ")
                                book_price = SVC_Amazon.strip_spaces(ele.span.text)
                                startpos = book_price.find("$")
                                book_price = SVC_Amazon.strip_spaces(
                                    book_price[startpos : len(book_price)]
                                )
                                # print("price1 ele: " + book_price)
                            except:
                                book_price = "$0.00"

                            # alt price
                            try:
                                ele = item.find(
                                    "a", attrs={"class": re.compile("a-size-mini*")}
                                )
                                book_price_alt = SVC_Amazon.strip_spaces(ele.text)
                                # print("price alt: " + book_price_alt)
                            except:
                                # print("book price alt fail")
                                book_price_alt = "None"

                            # load dict info
                            try:
                                book_details["price"] = book_price
                                book_details["price_alt"] = book_price_alt
                                book_categories[book_type] = str(book_details)
                                # print("---- details insert into category: "  + book_type + " count: " + str(count) )
                                # print("category " + book_type + " price " + book_price + " alt " + book_price_alt)
                                # print(" ")
                            except:
                                print("book insert crash")
                            # print("looping")

                        amz_page_data["book_categories_dict"] = str(book_categories)
                    except:
                        print("book type 1 fail ")
                        pass
                except:
                    print("tab1 fail")

            # end tab 1

            if tab2 == True:
                # type 2 of book tabs witb prices
                # print("tab type 2")
                div_content = body.find(
                    "div", attrs={"id": "mediaTabsGroup", "class": "feature"}
                )
                # print("div content " + div_content.prettify())
                ul_content = div_content.find("ul", attrs={"id": "mediaTabs_tabSet"})
                # print("ul content " + ul_content.prettify())

                try:
                    # each li is a book tab
                    li_items = ul_content.find_all(
                        "li", attrs={"id": re.compile("mediaTab_heading_*")}
                    )
                    for li in li_items:
                        # print(li.prettify())
                        book_type = ""
                        book_price = ""
                        book_price_alt = ""
                        count = count + 1
                        # get book type and price
                        try:
                            # type
                            ele = li.find(
                                "span", attrs={"class": "a-size-large mediaTab_title"}
                            )
                            # print(ele.prettify())
                            book_type = ele.text
                            # print("book type " + book_type)
                            if book_type.find("Audiobook") > 0:
                                book_type = "Audiobook"
                        except:
                            book_type = "book type error"
                        # get price
                        try:
                            ele = li.find(
                                "span", attrs={"class": "a-size-base mediaTab_subtitle"}
                            )
                            book_price = SVC_Amazon.strip_spaces(ele.text)
                            # print("price1 ele: ")
                        except:
                            error_code = error_code + "3pricefail"
                            # print("ele1 fail")
                            book_price = "$0.00"

                        # get alt price
                        try:
                            ele = li.find(
                                "a", attrs={"class": re.compile("a-size-mini*")}
                            )
                            book_price_alt = SVC_Amazon.strip_spaces(ele.text)
                            # print("price alt: " + book_price_alt)
                        except:
                            # print("Alt ")
                            book_price_alt = "None"

                        # load dict info
                        try:
                            # book_details["book_category_" + str(count)] = book_type
                            book_details["price"] = book_price
                            book_details["price_alt"] = "None"
                            book_categories[book_type] = str(book_details)
                            # print("---- details insert into category: "  + book_type + " count: " + str(count) )
                            # print("category " + book_type + " price " + book_price + " alt " + book_price_alt)
                            # print(" ")
                        except:
                            print("insert crash")
                    # print("looping")
                    # print("end for each")
                    amz_page_data["book_categories_dict"] = str(book_categories)
                except:
                    print("type2 fail")
                    pass
                # end tab 2
        # end check tab types
        except:
            error_code + error_code + " error_price"
            print("book type fail" + error_code)

        # get other recommend books
        try:
            ol_content = body.find("ol", attrs={"class": "a-carousel"})
            # print("dv")
            try:
                li_items = ol_content.find_all(
                    "li", attrs={"id": "", "class": "a-carousel-card", "style": ""}
                )
                recommend_details = {}
                recommend_books = {}
                count = 0
                try:
                    for item in li_items:
                        # print(item.a.prettify())
                        # print(strip_spaces(item.a.text))
                        item_text = SVC_Amazon.strip_spaces(item.a.text)
                        item_href = "https://www.amazon.com" + item.a["href"]
                        try:
                            recommend_details["title"] = item_text
                            recommend_details["href"] = item_href
                            # print("url = " + '"' + item_href + '"')
                            recommend_books[count] = str(recommend_details)
                            count = count + 1
                            if debug_0 == True:
                                print(
                                    "book details inserted" + str(recommend_details())
                                )
                        except:
                            if debug_0 == True:
                                print("book details insert failed")

                    try:
                        amz_page_data["recommend_books_dict"] = str(recommend_books)
                        if debug_0 == True:
                            print("product details inserted" + str(prod_details))
                    except:
                        if debug_0 == True:
                            print("product details insert failed" + str(prod_details))
                except:
                    amz_page_data["recommend_books_dict"] = "No details available"
                    if debug_0 == True:
                        print("product details not available")
            except:
                pass
        except:
            pass

        # get star rating
        try:
            div_content = body.find("div", attrs={"id": "averageCustomerReviews"})
            # print(div_content)
            temp_data = div_content.find(
                "i", attrs={"class": re.compile("a-icon a-icon-star a-star*")}
            )
            # print(temp_data)
            try:
                amz_page_data["book_rating"] = temp_data.span.text
                if debug_0 == True:
                    print("book rating inserted - " + temp_data.span.text)
            except:
                if debug_0 == True:
                    print("book rating insert failed - " + temp_data.span.text)

        except:
            amz_page_data["book_rating"] = "Not available"
            if debug_0 == True:
                print("book rating not found - " + temp_data)

        # load error code
        try:
            if error_code == "":
                error_code = "None"
            amz_page_data["error_code"] = error_code
        except:
            pass

        # ----------------------------

        # display dict info
        for x in amz_page_data:
            try:
                print(x + " - " + amz_page_data[x])
            except:
                pass

        # print(text_data)
        return amz_page_data

    def strip_spaces(temp_data):
        spam_fried = False
        stripped_string = ""
        if len(temp_data) < 2:
            return temp_data
        for elem in temp_data[0 : len(temp_data) : 1]:
            # print(ord(elem))
            if ord(elem) > 32 and ord(elem) <= 125:
                stripped_string = stripped_string + elem
                spam_fried = False
            elif ord(elem) == 32 and spam_fried == False:
                stripped_string = stripped_string + " "
                spam_fried = True
        return stripped_string

    def strip_code(temp_data):
        # print("trystrip")
        try:
            startpos = temp_data.find("{")
            endpos = temp_data.find("}")
            # print("stripping")
            if startpos > 0 and endpos > 0:
                temp_data = (
                    temp_data[0 : startpos - 1]
                    + " "
                    + temp_data[endpos + 1 : len(temp_data)]
                )
                # print("stripped")
        except:
            pass
        return temp_data

    def strip_tail(temp_data):
        for lp in temp_data:
            if (
                temp_data[-1] == " "
                or temp_data[-1] == ","
                or temp_data[-1] == ":"
                or (ord(temp_data[-1]) <= 32 or ord(temp_data[-1]) >= 125)
            ):
                temp_data = temp_data[:-1]
            else:
                break
        return temp_data

    def strip_head(temp_data):
        for lp in temp_data:
            if temp_data[0] == " " or temp_data[0] == "," or temp_data[0] == ":":
                temp_data = temp_data[1:]
            else:
                break

        return temp_data
