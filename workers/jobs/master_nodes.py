import os
import requests
from glom import glom, Literal
from common import CertsClass


def nodes_sync(master_id, master_address):
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
        nodes_uri = f"https://{master_address}:8081/v4/nodes"
    else:
        # PuppetDB >= 3.x
        nodes_uri = f"https://{master_address}:8081/pdb/query/v4/nodes"
    req = requests.get(nodes_uri, verify=False, cert=(cert_path, private_key_path))
    target = req.json()
    spec = [{"certname": "certname", "master_zone": Literal(master_id)}]
    user = os.environ.get("WEBAPP_USER", "")
    password = os.environ.get("WEBAPP_PASS", "")
    requests.post(
        "http://webapp:8000/api/nodes/sync/",
        json=glom(target, spec),
        auth=(user, password),
    )
