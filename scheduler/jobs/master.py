import os
import faktory
import requests


def enqueue_update():
    user = os.environ.get("WEBAPP_USER", "")
    password = os.environ.get("WEBAPP_PASS", "")
    req = requests.get('http://webapp:8000/api/master_zones/', auth=(user, password))
    for master_json in req.json():
        with faktory.connection() as client:
            client.queue('master-environments', args=(master_json['id'],)),
            client.queue('master-facts', args=(master_json['id'], master_json['address']))
            client.queue('master-nodes', args=(master_json['id'], master_json['address']))
            client.queue('master-classes', args=(master_json['id'], master_json['environments_names']))
