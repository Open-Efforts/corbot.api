import json
import re

LOG_FILE = "logs/uwsgi.log"
TARGET_JSON_FILE = "tests/actions.json"


def get_all_requests_from_log(log_file=LOG_FILE, target_json_file=TARGET_JSON_FILE):
    """[summary] read all log file and put all found request data to JSON
    """
    method_pattern = re.compile(r"method name:\s*(?P<method>\w+)")
    body_pattern = re.compile(r"body:\s*(?P<body>\w+)")
    regnum_pattern = re.compile(r"reg_num:\s*(?P<reg_num>\w+)")
    # re.search(r'(?<=-)\w+', 'spam-egg')
    all_actions = []
    with open(log_file, "r") as f:
        action = {}
        for line in f.readlines():
            line = line.strip()
            # print(line)
            res = method_pattern.search(line)
            if res:
                action["subject"] = res.group("method")
                continue
            res = body_pattern.search(line)
            if res:
                action["body"] = res.group("body")
                continue
            res = regnum_pattern.search(line)
            if res:
                action["reg_number"] = res.group("reg_num")
                all_actions += [action]
                action = {}
                continue
    with open(target_json_file, "w") as f:
        json.dump(all_actions, f, indent=2)


def play_actions(app, json_file=TARGET_JSON_FILE):
    with app.test_client() as client:
        # app_ctx = app.app_context()
        # app_ctx.push()
        with open(json_file, "r") as f:
            actions = json.load(f)
            for action in actions:
                response = client.post('/api', json=action)
                assert response.status_code == 200
        # app_ctx.pop()
