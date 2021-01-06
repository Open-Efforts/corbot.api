from sqlalchemy import Table

from app import metadata


class SVC_Info:
    def cmd_info(arg):
        cb_info = Table("cb_info", metadata, autoload=True)
        qry = cb_info.select().where(cb_info.c.info_keyword == arg)
        results = qry.execute()
        message_rows = {}
        data = ""
        cnt = 0
        for row in results:
            info_row = dict(row)
            info_id = info_row["info_id"]
            info_subject = info_row["info_subject"]
            info_text = info_row["info_text"]
            info_text = str(info_text)
            info_text = info_text.replace(r"\r\n", chr(13) + chr(10))
            info_text = info_text.replace(r"\t", " ")
            cnt += 1
        if cnt == 0:
            info_subject = "Info: Error"
            info_text = (
                "Apologies: we do not have any information pages listed via the search phrase: "
                + str(arg)
            )
        return info_subject, info_text
