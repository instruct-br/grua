import os
import requests
from common import CertsClass


def facts_sync(master_id, master_address):
    cert_instance = CertsClass(master_id)
    cert_path = cert_instance.get_cert()
    private_key_path = cert_instance.get_key()
    req = requests.get(
        f"https://{master_address}:8081/pdb/meta/v1/version",
        verify=False,
        cert=(cert_path, private_key_path),
    )
    if req.status_code == 404:
        # PuppetDB <= 2.x
        facts_uri = f"https://{master_address}:8081/v4/fact-names"
    else:
        # PuppetDB >= 3.x
        facts_uri = f"https://{master_address}:8081/pdb/query/v4/fact-names"
    req = requests.get(facts_uri, verify=False, cert=(cert_path, private_key_path))
    facts = [{"name": fact, "master_zone": master_id} for fact in req.json()]
    user = os.environ.get("WEBAPP_USER", "")
    password = os.environ.get("WEBAPP_PASS", "")
    requests.post(
        "http://webapp:8000/api/facts/sync/", json=facts, auth=(user, password)
    )
