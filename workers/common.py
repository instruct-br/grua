import os
import requests
from tempfile import NamedTemporaryFile


class CertsClass:

    def __init__(self, master_id=None):
        user = os.environ.get("WEBAPP_USER", "")
        password = os.environ.get("WEBAPP_PASS", "")
        self.master_data = requests.get(
            f"http://webapp:8000/api/master_zones/{master_id}", auth=(user, password)
        ).json()

    def _download_file(self, url):
        if not url:
            return None
        req = requests.get(url)
        downloaded_file = NamedTemporaryFile(delete=False)
        downloaded_file.write(req.content)
        downloaded_file.close()
        return downloaded_file.name

    def get_cert(self):
        return self._download_file(self.master_data["signed_cert"])

    def get_key(self):
        return self._download_file(self.master_data["private_key"])

    def get_master_address(self):
        return self.master_data["address"]
