import datetime
from datetime import timedelta
import json
import requests
import pytz
from sqlalchemy import Table

from app import metadata, session


class SVC_Rundown:
    def get_sport_id_and_name(body):
        body_list = str(body).lower().split(" ")
        ncaa_foot_list = ["NCAA Football", "ncaa football", "ncaa", "1"]
        nfl_list = ["NFL", "nfl", "2", "nlf"]
        mlb_list = ["MLB", "3", "mlb", "mbl", "baseball"]
        nba_list = ["NBA", "nba", "4", "nab"]
        ncaa_mens_bb_list = [
            "NCAA Men's Basketball",
            "ncaa mens basketball",
            "ncaa men's basketball",
            "5",
        ]
        nhl_list = ["NHL", "6", "nhl", "nlh"]
        ufc_list = ["UFC/MMA", "7", "mma", "ufc", "ufc/mma", "mam", "ucf"]
        wnba_list = ["WNBA", "wnba", "8", "wbna"]
        cfl_list = ["CFL", "cfl", "clf", "9"]
        mls_ist = ["MLS", "10", "msl", "mls", "soccer"]
        sport_dict = {
            "1": ncaa_foot_list,
            "2": nfl_list,
            "3": mlb_list,
            "4": nba_list,
            "5": ncaa_mens_bb_list,
            "6": nhl_list,
            "7": ufc_list,
            "8": wnba_list,
            "9": cfl_list,
            "10": mls_ist,
        }
        sport_id = 0
        sport_name = ""
        for word in body_list:
            for k, v in sport_dict.items():
                if word in v:
                    sport_id = int(k)
                    sport_name = v[0]
        return sport_id, sport_name

    def cmd_odds(sport):
        try:
            # Figure Out the Sport Code
            todays_date = datetime.datetime.now()
            week_out = todays_date + timedelta(days=7)
            sport_id, sport_name = SVC_Rundown.get_sport_id_and_name(sport)

            # Get Rundown Odds Data
            if sport_id == 0:
                msg_subject, odds_info = SVC_Rundown.get_notice(16, metadata)
            else:
                msg_subject = "Sports: " + sport_name
                url = f"https://www.corbot.us/data/odds-{sport_id}.json"
                body_text = ""
                r = requests.get(
                    url,
                    headers={
                        "User-agent": "Mozilla/5.0 (X11; Linux i686; rv:64.0) Gecko/20100101 Firefox/70.0"
                    },
                )

                j_data = json.loads(r.text)
                data = j_data["data"]
                odds_info = "\n"
                for date in data:
                    events = date["events"]
                    if len(events) > 0:
                        game_data = {}
                        for event_data in events:
                            game_data["event_id"] = event_data["event_id"]
                            game_data["sport_id"] = event_data["sport_id"]

                            # get date and time
                            game_data["event_date"] = event_data["event_date"]
                            game_date = game_data["event_date"].split("T")[0]
                            game_date_date = datetime.datetime.strptime(
                                game_date, "%Y-%m-%d"
                            )
                            game_time = (
                                game_data["event_date"]
                                .split("T")[1]
                                .replace(":00Z", "")
                            )
                            game_time = datetime.datetime.strptime(game_time, "%H:%M")
                            # function to see if its DST in CST

                            def is_dst(time_arg, tz_arg):
                                tz_arg = pytz.timezone(tz_arg)
                                tz_arg_aware_date = tz_arg.localize(
                                    time_arg, is_dst=None
                                )
                                return tz_arg_aware_date.tzinfo._dst.seconds != 0

                            if is_dst(game_date_date, "US/Central") == True:
                                game_time = game_time - timedelta(hours=5)
                            else:
                                game_time = game_time - timedelta(hours=6)
                            game_time = game_time.strftime("%I:%M %p")

                            score_data = event_data["score"]
                            if "teams" in event_data:
                                team_data = event_data["teams"]
                                team_data0 = team_data[0]
                                team_data1 = team_data[1]
                                if team_data0["is_home"] is True:
                                    game_data["home_name"] = team_data0["name"]
                                    game_data["away_name"] = team_data1["name"]
                                else:
                                    game_data["home_name"] = team_data1["name"]
                                    game_data["away_name"] = team_data0["name"]
                            else:
                                team_data = event_data["teams_normalized"]
                                team_data0 = team_data[0]
                                team_data1 = team_data[1]
                                if team_data0["is_home"] is True:
                                    game_data["home_name"] = (
                                        team_data0["name"] + " " + team_data0["mascot"]
                                    )
                                    game_data["away_name"] = (
                                        team_data1["name"] + " " + team_data1["mascot"]
                                    )
                                else:
                                    game_data["home_name"] = (
                                        team_data1["name"] + " " + team_data1["mascot"]
                                    )
                                    game_data["away_name"] = (
                                        team_data0["name"] + " " + team_data0["mascot"]
                                    )

                            score_data["event_status"] = (
                                score_data["event_status"].split("_")[1].lower().title()
                            )

                            aff_cnt = 1
                            if "lines" in event_data:
                                affiliate_names = []
                                home_spreads = []
                                away_spreads = []
                                total = []
                            else:
                                affiliate_names = ["No data"]
                                home_spreads = ["No data"]
                                away_spreads = ["No data"]
                                total = ["No data"]
                            if "lines" in event_data:
                                line_data = event_data["lines"]
                                for k, v in line_data.items():
                                    if aff_cnt <= 5:
                                        affiliates_data = dict(v)
                                        spread_data = affiliates_data["spread"]
                                        total_data = affiliates_data["total"]
                                        total_over = total_data["total_over"]

                                        # if spread or total is a pulled line
                                        if total_over == 0.0001:
                                            total_over = "No data"
                                        if spread_data["point_spread_home"] == 0.0001:
                                            spread_data["point_spread_home"] = "No data"
                                        if spread_data["point_spread_away"] == 0.0001:
                                            spread_data["point_spread_away"] = "No data"

                                        game_data["point_spread_home"] = spread_data[
                                            "point_spread_home"
                                        ]
                                        game_data["point_spread_away"] = spread_data[
                                            "point_spread_away"
                                        ]
                                        aff_data = affiliates_data["affiliate"]
                                        aff_name = aff_data["affiliate_name"]

                                        affiliate_names.append(aff_name)
                                        aff_cnt += 1
                                        if (
                                            spread_data["point_spread_home"]
                                            != "No data"
                                            and aff_cnt < 5
                                        ):
                                            home_spreads.append(
                                                str(game_data["point_spread_home"])
                                            )
                                        else:
                                            home_spreads.append(
                                                str(game_data["point_spread_home"])
                                            )
                                        if (
                                            spread_data["point_spread_away"]
                                            != "No data"
                                            and aff_cnt < 5
                                        ):
                                            away_spreads.append(
                                                str(game_data["point_spread_away"])
                                            )
                                        else:
                                            away_spreads.append(
                                                str(game_data["point_spread_away"])
                                            )
                                        if total_over != "No data" and aff_cnt < 5:
                                            total.append(str(total_over))
                                        else:
                                            total.append(str(total_over))

                            if game_date_date <= week_out:
                                odds_info += (
                                    "Time: "
                                    + str(game_date)
                                    + " at "
                                    + str(game_time)
                                    + "\n"
                                    + "Home: "
                                    + game_data["home_name"]
                                    + " | Spread: "
                                    + home_spreads[0]
                                    + "\n"
                                    "Away: "
                                    + game_data["away_name"]
                                    + " | Spread: "
                                    + away_spreads[0]
                                    + "\n"
                                    + "Over/Under: "
                                    + total[0]
                                    + "\n\n"
                                )

            if len(odds_info) < 16:
                msg_subject = "Sports: Error"
                odds_info = (
                    "There is no event data for " + sport_name + " at this time."
                )
            return msg_subject, odds_info
        except Exception as e:
            msg_subject = "Error"
            msg_body = "There was an issue with the server: " + str(e)
            return msg_subject, msg_body

    @staticmethod
    def cmd_scores(sport, metadata, session):
        try:
            # Figure Out the Sport Code
            sport_id, sport_name = SVC_Rundown.get_sport_id_and_name(sport)
            # Get Rundown Sports Data
            if sport_id == 0:
                msg_subject, msg_body = SVC_Rundown.get_notice(16, metadata)
            else:
                msg_subject = "Sports: " + sport_name
                url = f"https://www.corbot.us/data/scores-{sport_id}-yesterday.json"
                body_text = "Game Data:\r"
                r = requests.get(
                    url,
                    headers={
                        "User-agent": "Mozilla/5.0 (X11; Linux i686; rv:64.0) Gecko/20100101 Firefox/70.0"
                    },
                )

                j_data = json.loads(r.text)
                meta = j_data["meta"]
                events = j_data["events"]
                game_data = {}

                for row in events:
                    event_data = dict(row)
                    game_data["event_id"] = event_data["event_id"]
                    game_data["sport_id"] = event_data["sport_id"]
                    game_data["event_date"] = event_data["event_date"]
                    score_data = event_data["score"]
                    if "teams" in event_data:
                        team_data = event_data["teams"]
                        team_data0 = team_data[0]
                        team_data1 = team_data[1]
                        if team_data0["is_home"] is True:
                            game_data["home_name"] = team_data0["name"]
                            game_data["away_name"] = team_data1["name"]
                        else:
                            game_data["home_name"] = team_data1["name"]
                            game_data["away_name"] = team_data0["name"]
                    else:
                        team_data = event_data["teams_normalized"]
                        team_data0 = team_data[0]
                        team_data1 = team_data[1]
                        if team_data0["is_home"] is True:
                            game_data["home_name"] = (
                                team_data0["name"] + " " + team_data0["mascot"]
                            )
                            game_data["away_name"] = (
                                team_data1["name"] + " " + team_data1["mascot"]
                            )
                        else:
                            game_data["home_name"] = (
                                team_data1["name"] + " " + team_data1["mascot"]
                            )
                            game_data["away_name"] = (
                                team_data0["name"] + " " + team_data0["mascot"]
                            )
                    body_text += (
                        "Home: "
                        + game_data["home_name"]
                        + " | "
                        + "Away: "
                        + game_data["away_name"]
                        + "\n"
                    )
                    body_text += (
                        "Scores:  Home: "
                        + str(score_data["score_home"])
                        + " | "
                        + " Away: "
                        + str(score_data["score_away"])
                        + "\n"
                    )
                    body_text += (
                        "Venue Name: "
                        + score_data["venue_name"]
                        + " | "
                        + "Location: "
                        + score_data["venue_location"]
                        + "\n"
                    )

                    body_text += "\n"
                msg_body = body_text
            if len(msg_body) < 16:
                msg_subject = "Scores: Error"
                msg_body = "There is no score data for " + sport_name + " at this time."
            return msg_subject, msg_body
        except Exception as e:
            msg_subject = "Error"
            msg_body = "There was an issue with the server: " + str(e)
            return msg_subject, msg_body

    @staticmethod
    def get_notice(notice_id, metadata):
        notices = Table("notices", metadata, autoload=True)
        qry = notices.select().where(notices.c.notice_id == notice_id).limit(1)
        results = qry.execute()
        notice_data = {}
        for row in results:
            notice_data = dict(row)
        return notice_data["notice_subject"], notice_data["notice_text"]
