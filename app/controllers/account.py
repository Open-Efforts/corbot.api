from app import metadata, session

from sqlalchemy import Table
from loguru import logger


class SVC_Account:
    def cmd_account(regnum):
        reg_num = str(regnum)
        subject = "Account Information"
        client_data = SVC_Account.get_client_data(reg_num, metadata)
        client_name = client_data["f_name"] + " " + client_data["l_name"]
        client_id = client_data["client_id"]
        plan_id = client_data["plan_id"]
        plan_data = SVC_Account.get_plan_data(plan_id, metadata)
        plan_name = plan_data["plan_name"]
        start_date = client_data["date_added"]
        days_remaining = client_data["days_remaining"]
        account_data = "Your Current Account Data:" + "\r\r"
        account_data += "Name: " + client_name + "\r"
        account_data += "Number: " + reg_num + "\r"
        account_data += "Client ID: " + str(client_id) + "\r"
        account_data += "Personal Email: " + client_data["email_address"] + "\r"
        account_data += "Account Type: " + plan_name + "\r"
        account_data += "Start Date: " + str(start_date) + "\r"
        # account_data += "Days Remaining: " + str(days_remaining) + "\r"
        account_data += "Expiration Date: " + str(client_data["expire_date"]) + "\r\r"
        # Show Account History
        account_data += "---------------- Account History ------------------ \r"
        account_data += SVC_Account.get_account_history(client_id, metadata)
        # Show Blocked
        blocked_text = SVC_Account.get_blocked(client_id, metadata)
        if len(blocked_text) > 1:
            account_data += "\r ---------------- Blocked Contacts------------------ \r"
            account_data += blocked_text

        # Add SMS Data if it exists
        sms_out_msgs = SVC_Account.get_sms_out(client_id, metadata)
        if len(sms_out_msgs) > 0:
            account_data += "\r---------------- Message History ------------------ \r"
            account_data += "\rOutbound SMS (last 25): \r"
            for msg_row in sms_out_msgs:
                account_data += (
                    str(msg_row["sms_out_id"])
                    + " | "
                    + str(msg_row["stamp"])
                    + " to "
                    + msg_row["sms_dst"]
                    + " "
                    + msg_row["message_state"]
                    + "\r"
                )
        sms_in_msgs = SVC_Account.get_sms_in(client_id, metadata)
        if len(sms_in_msgs) > 0:
            account_data += "\r\rInbound SMS (last 25): \r"
            for msg_row in sms_in_msgs:
                account_data += (
                    str(msg_row["sms_in_id"])
                    + " | "
                    + str(msg_row["received"])
                    + " from "
                    + msg_row["sms_src"]
                    + " received"
                    + "\r"
                )
        account_data += "\r This is your account status page, you can request a copy of this page at any time by sending a request with Account in the subject line, and Status in the body."
        return subject, account_data

    def get_blocked(client_id, metadata):
        blocks = Table("blocks", metadata, autoload=True)
        qry = blocks.select().where(blocks.c.client_id == client_id)
        res = qry.execute()
        block_list_text = ""
        for row in res:
            block_data = dict(row)
            show_row = (
                str(block_data["block_id"])
                + " "
                + str(block_data["phone_number"])
                + " "
                + str(block_data["date_added"])
                + "\r"
            )
            logger.debug(show_row)
            block_list_text += str(show_row)
        return block_list_text

    def get_account_history(client_id, metadata):
        client_trans = Table("client_trans", metadata, autoload=True)
        qry = (
            client_trans.select()
            .where(client_trans.c.client_id == client_id)
            .order_by(client_trans.c.stamp.desc())
        )
        res = qry.execute()
        account_history = "\r\n   date.....method.....plan.....qty.....period.....unit-price.....days\r\n"
        for row in res:
            trans_data = dict(row)
            if trans_data["plan_id"] == 3:
                trans_data["plan_name"] = "Trial"
            elif trans_data["plan_id"] == 4:
                trans_data["plan_name"] = "bronze"
            elif trans_data["plan_id"] == 5:
                trans_data["plan_name"] = "silver"
            elif trans_data["plan_id"] == 6:
                trans_data["plan_name"] = "gold"
            elif trans_data["plan_id"] == 7:
                trans_data["plan_name"] = "platinum"
            else:
                trans_data["plan_name"] = "---"
            show = (
                str(trans_data["stamp"].date())
                + "....."
                + str(trans_data["pay_method"])
                + "....."
                + str(trans_data["plan_name"])
                + "....."
                + str(trans_data["qty"])
                + "....."
                + str(trans_data["period"])
                + "....."
                + str(trans_data["unit_price"])
                + "....."
                + str(trans_data["days"])
                + "\r\n"
            )
            account_history = account_history + show
        return account_history

    def get_client_data(reg_num, metadata):
        clients = Table("clients", metadata, autoload=True)
        qry = clients.select().where(clients.c.reg_num == reg_num).limit(1)
        results = qry.execute()
        client_data = {}
        for row in results:
            client_data = dict(row)
        return client_data

    def get_plan_data(plan_id, metadata):
        plans = Table("plans", metadata, autoload=True)
        qry = plans.select().where(plans.c.plan_id == plan_id).limit(1)
        results = qry.execute()
        lowest_price = 0
        plan_data = {}
        for row in results:
            plan_row = dict(row)
        return plan_row

    def get_balance(client_id, metadata):
        transactions = Table("transactions", metadata, autoload=True)
        qry = transactions.select().where(transactions.c.client_id == client_id)
        results = qry.execute()
        balance = 0
        for row in results:
            plan_row = dict(row)
            if plan_row["trans_type"] == "C":
                balance = balance + plan_row["credit"]
            if plan_row["trans_type"] == "D":
                balance = balance - plan_row["debit"]
        balance = "%.2f" % balance
        return balance

    def get_sms_out(client_id, metadata):
        sms_outbound = Table("sms_outbound", metadata, autoload=True)
        qry = (
            sms_outbound.select()
            .where(sms_outbound.c.client_id == client_id)
            .order_by(sms_outbound.c.sms_out_id.desc())
            .limit(25)
        )
        res = qry.execute()
        sms_list = []
        for sms_msg in res:
            sms_list.append(sms_msg)
        return sms_list

    def get_sms_in(client_id, metadata):
        sms_inbound = Table("sms_inbound", metadata, autoload=True)
        qry = (
            sms_inbound.select()
            .where(sms_inbound.c.client_id == client_id)
            .order_by(sms_inbound.c.sms_in_id.desc())
            .limit(25)
        )
        res = qry.execute()
        sms_list = []
        for sms_msg in res:
            sms_list.append(sms_msg)
        return sms_list
