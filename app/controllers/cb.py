import email
import re

import pandas as pd
from loguru import logger
from sqlalchemy import Table

from app import metadata, session


class CB:
    def unparse_contact_name(subject: str):
        contact_name = None
        if (subject.find("[") >= 0) and (subject.find("]") >= 0):
            contact_used = 1
            logger.debug("Found some square brackets...")
            pos1 = subject.find("[") + 1
            pos2 = subject.find("]")
            contact_name = subject[pos1:pos2].strip().lower()
        elif (subject.find("{") >= 0) and (subject.find("}") >= 0):
            contact_used = 1
            logger.debug("Found some moustache brackets...")
            pos1 = subject.find("{") + 1
            pos2 = subject.find("}")
            contact_name = subject[pos1:pos2].strip().lower()
        elif (subject.find("(") >= 0) and (subject.find(")") >= 0):
            contact_used = 1
            logger.debug("Found some parethetical brackets...")
            pos1 = subject.find("(") + 1
            pos2 = subject.find(")")
            contact_name = subject[pos1:pos2].strip().lower()
        if contact_name:
            contact_name = contact_name.strip().lower()

        return contact_name

    def check_contact(client_id, contact_name):
        contacts = Table("contacts", metadata, autoload=True)
        qry = (
            contacts.select()
            .where(contacts.c.client_id == client_id)
            .where(contacts.c.contact_name == contact_name)
        )
        res = qry.execute()
        rowcount = len(res._saved_cursor._result.rows)
        contact_did = None
        if rowcount > 0:
            found = 1
            for row in res:
                contact_data = dict(row)
        else:
            found = 0
            contact_data = {}
        return found, contact_data

    def get_contact_data(client_id, contact_name):
        contacts = Table("eml_contacts", metadata, autoload=True)
        qry = (
            contacts.select()
            .where(contacts.c.client_id == client_id)
            .where(contacts.c.contact_name == contact_name)
        )
        res = qry.execute()
        contact_data = {}
        contact_data["contact_id"] = 0
        for row in res:
            contact_data = dict(row)
        return contact_data

    def build_msg_lists(cbobj, node_id):
        # Spin a list of all New Inbound Messages
        in_rows = CB.get_unrouted_inbound(cbobj, node_id)
        logger.info(
            "There are "
            + str(len(in_rows))
            + " total messages to process from Inbound."
        )
        signup_node_list = CB.get_signup_nodes(cbobj)
        msg_list_1 = []
        bounce_list = []
        skip_list = []
        send_list = []
        # Add the Check for CorrLink Messages....! ! !
        for msg_row in in_rows:
            msg_data = dict(msg_row)
            msg_data["decision_tree"] = ""
            msg_data["subject"] = str(msg_data["subject"]).lower()
            # Continue Thread or Hack Off
            chk_support = msg_data["subject"].find("support")
            chk_alfred = msg_data["subject"].find("alfred")
            if (chk_support >= 0) or (chk_alfred >= 0):
                msg_data["needs_human"] = 1
                is_support = 1
            else:
                msg_data["message"] = CB.get_phrase(msg_data["message"])
                msg_data["needs_human"] = 0
            # Check to see if it's an Account Requests
            chk_account = msg_data["subject"].find("account")
            chk_balance = msg_data["subject"].find("balance")
            chk_payment = msg_data["subject"].find("payment")
            # Loop through the Messages and Sort Conditionally
            if (
                (chk_support >= 0)
                or (chk_account >= 0)
                or (chk_balance >= 0)
                or (chk_payment >= 0)
            ):
                msg_data["needs_human"] = 1
                msg_data["dst"] = "cb"
                send_list.append(msg_data)
            elif msg_data["expired"] == 1:
                # Bounce - Expired
                msg_data["dst"] = "cb"
                msg_data["bounce"] = 1
                msg_data["notice_id"] = 31
                bounce_list.append(msg_data)
            elif msg_data["plan_id"] < 2:
                msg_data["dst"] = "cb"
                msg_data["bounce"] = 1
                msg_data["notice_id"] = 31
                bounce_list.append(msg_data)
            elif msg_row["node_id"] in signup_node_list:
                # Bounce - Sign-Up Node
                msg_data["dst"] = "cb"
                msg_data["bounce"] = 1
                msg_data["notice_id"] = 29
                bounce_list.append(msg_data)
            elif len(str(msg_data["message"])) == 0:
                # Bounce - Blank Message
                msg_data["dst"] = "cb"
                msg_data["bounce"] = 1
                msg_data["notice_id"] = 30
                bounce_list.append(msg_data)
            else:
                msg_list_1.append(msg_data)

        # Establish Message Type and Manage Rejections
        msg_list_2 = []
        for msg_row in msg_list_1:
            msg_data = dict(msg_row)
            msg_data["decision_tree"] = ""

            # Check for SMS by trying to build a number out of the subject
            did = "".join([n for n in msg_data["subject"] if n.isdigit()])
            if len(str(did)) == 10:
                did = "1" + did

            # ----- Contact Manager Message Update -----
            new_body = msg_data["message"]
            if (str(msg_data["subject"]).find("[") >= 0) and (
                str(msg_data["subject"]).find("]") >= 0
            ):
                contact_used = 1
                logger.debug("Found some square brackets...")
                pos1 = str(msg_data["subject"]).find("[") + 1
                pos2 = str(msg_data["subject"]).find("]")
                contact_name = str(msg_data["subject"])[pos1:pos2].strip().lower()
            # ---------- comment out everything between the here and...
            elif (str(msg_data["subject"]).find("{") >= 0) and (
                str(msg_data["subject"]).find("}") >= 0
            ):
                contact_used = 1
                logger.debug("Found some moustache brackets...")
                pos1 = str(msg_data["subject"]).find("{") + 1
                pos2 = str(msg_data["subject"]).find("}")
                contact_name = str(msg_data["subject"])[pos1:pos2].strip().lower()
            elif (str(msg_data["subject"]).find("(") >= 0) and (
                str(msg_data["subject"]).find(")") >= 0
            ):
                contact_used = 1
                logger.debug("Found some parethetical brackets...")
                pos1 = str(msg_data["subject"]).find("(") + 1
                pos2 = str(msg_data["subject"]).find(")")
                contact_name = str(msg_data["subject"])[pos1:pos2].strip().lower()
            # -------- here, if things go South with the Contacts
            elif str(msg_data["subject"]).strip() == "-":
                contact_used = 1
                pos1 = str(msg_data["message"]).find(",")
                contact_name = str(msg_data["message"])[:pos1]
                new_body = str(msg_data["message"])[pos1 + 1 :]
            else:
                # Not Using Contact Manager
                contact_used = 0
                contact_found = 0
                contact_name = str(msg_data["subject"]).strip().lower()
            # -----
            contact_name = contact_name.strip().lower()
            logger.debug(
                "Checking contact for Client ID: "
                + str(msg_data["client_id"])
                + " using contact name "
                + contact_name
            )
            contact_found, contact_data = CB.check_contact(
                cbobj, msg_data["client_id"], contact_name
            )
            logger.debug("Contact Data: " + str(contact_data))
            # -----
            if contact_found == 1:
                if contact_data["contact_type"] == "number":
                    logger.debug(
                        "SMS Contact found for "
                        + contact_data["contact_name"]
                        + ": "
                        + contact_data["phone_number"]
                    )
                    did = contact_data["phone_number"]
                    msg_data["subject"] = contact_data["phone_number"]
                    msg_data["message"] = new_body
                    msg_data["dst_did"] = contact_data["phone_number"]
                if contact_data["contact_type"] == "email":
                    logger.debug(
                        "Email Contact found for "
                        + contact_data["contact_name"]
                        + ": "
                        + contact_data["email_address"]
                    )
                    msg_data["subject"] = contact_data["email_address"]
                    msg_data["message"] = new_body
                    msg_data["dst_email"] = contact_data["email_address"]
            else:
                logger.debug("No contact found for contact name " + contact_name)

            # ------------------------------------------------------------------------

            # Sort Messages Conditionally
            if (contact_found == 0) and (contact_used == 1):
                # Client tried to use a contact, but no contact was found. Send an error message.
                msg_data["bounce"] = 1
                msg_data["notice_id"] = 36
                bounce_list.append(msg_data)
            elif len(str(did)) == 11:
                logger.debug("Setting message to go to: SMS")
                msg_data["dst"] = "sms"
                msg_data["dst_did"] = did
                msg_list_2.append(msg_data)
            elif len(str(did)) > 11:
                logger.debug("Setting message to go to: SMS")
                msg_data["bounce"] = 1
                msg_data["notice_id"] = 32
                bounce_list.append(msg_data)
            elif re.match("[^@]+@[^@]+\.[^@]+", msg_data["subject"]):
                logger.debug("Setting message to go to: Email")
                msg_data["dst"] = "eml"
                msg_data["dst_email"] = msg_data["subject"]
                msg_list_2.append(msg_data)
            # elif (contact_found) and (contact_data["contact_type"] == "number"):
            #     logger.debug("Building: Contact SMS")
            #     msg_data["dst"] = "sms"
            #     msg_data["dst_did"] = contact_did
            #     msg_data["subject"] = contact_did
            #     msg_list_2.append(msg_data)
            # elif (contact_found)and (contact_data["con"]):
            #     logger.debug("Building: Contact Email")
            #     msg_data["dst"] = "eml"
            #     msg_data["dst_email"] = contact_email
            #     msg_data["subject"] = contact_email
            #     msg_list_2.append(msg_data)
            else:
                logger.debug("Setting message to go to: Email")
                msg_data["dst"] = "cb"
                msg_list_2.append(msg_data)

        # Build Client Limit Sets
        client_regnum__list = []
        for msg_row in msg_list_2:
            msg_data = dict(msg_row)
            reg_num = msg_data["reg_num"]
            client_regnum__list.append(reg_num)
        client_regnum__list = set(client_regnum__list)

        # Check Messages Available and Update Values
        client_list = []
        for reg_num in client_regnum__list:
            client_data = {}
            client_data["reg_num"] = reg_num
            client_data["msgs_available"] = 50
            client_list.append(client_data)
        df_clients = pd.DataFrame(client_list)

        # Check for Limits and Skip Limited Message
        for msg_row in msg_list_2:
            msg_data = dict(msg_row)
            reg_num = msg_data["reg_num"]
            msgs_available = msg_data["msgs_available"]
            # Adding a fixed message daily limit to everyone for now
            # msgs_available = 20
            client_row = df_clients.loc[df_clients["reg_num"] == reg_num]
            the_value = int(client_row["msgs_available"])

            if the_value == 50:
                for index, row in df_clients.iterrows():
                    if df_clients.loc[index, "reg_num"] == reg_num:
                        df_clients.at[index, "msgs_available"] = msgs_available
            else:
                for index, row in df_clients.iterrows():
                    if df_clients.loc[index, "reg_num"] == reg_num:
                        df_clients.at[index, "msgs_available"] = msgs_available - 1

            client_row = df_clients.loc[df_clients["reg_num"] == reg_num]
            the_value = int(client_row["msgs_available"])

            if (the_value < 1) and (msg_data["dst"] == "cb"):
                skip_list.append(msg_data)
            else:
                send_list.append(msg_data)

        return send_list, bounce_list, skip_list
