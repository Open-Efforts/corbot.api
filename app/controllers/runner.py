from sqlalchemy import Table

from app import metadata, session


class Runner:
    def service_ident(msg_subject):
        subject = str(msg_subject)
        subject = subject.lower().strip()
        svc_keys = Table("svc_keys", metadata, autoload=True)
        qry = svc_keys.select()
        res = qry.execute()
        svc_requested = "unknown"
        for svc_row in res:
            svc_data = dict(svc_row)
            svc_name = svc_data["svc_name"]
            svc_phrases = svc_data["svc_phrases"]
            pos1 = svc_phrases.find(subject)
            if pos1 >= 0:
                svc_requested = svc_name
        return svc_requested

    def get_client_id(reg_num):
        clients = Table("clients", metadata, autoload=True)
        qry = clients.select().where(clients.c.reg_num == reg_num).limit(1)
        results = qry.execute()
        client_data = {}
        client_id = 0
        for row in results:
            client_row = dict(row)
            client_id = client_row["client_id"]
        return client_id

    def get_client(client_id):
        clients = Table("clients", metadata, autoload=True)
        qry = clients.select().where(clients.c.client_id == client_id).limit(1)
        res = qry.execute()
        client_data = {}
        for row in res:
            client_data = dict(row)
        return client_data
