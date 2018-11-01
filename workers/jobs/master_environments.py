import os
import requests
from common import CertsClass


def environments_sync(master_id):
    cert_instance = CertsClass(master_id)
    cert_path = cert_instance.get_cert()
    private_key_path = cert_instance.get_key()
    master_address = cert_instance.get_master_address()

    req = requests.get(
        f"https://{master_address}:8140/puppet/v3/environments",
        verify=False,
        cert=(cert_path, private_key_path),
    )
    environments_dict = req.json()["environments"]
    data = {
        "master_id": master_id,
        "environments": [environment for environment, _ in environments_dict.items()],
    }

    user = os.environ.get("WEBAPP_USER", "")
    password = os.environ.get("WEBAPP_PASS", "")
    requests.post(
        "http://webapp:8000/api/master_zones/environments_sync/",
        json=data,
        auth=(user, password),
    )
