import os
from itertools import chain
import requests
from glom import glom, Literal, Coalesce
from common import CertsClass


def classes_sync(master_id, environments):
    cert_instance = CertsClass(master_id)
    cert_path = cert_instance.get_cert()
    private_key_path = cert_instance.get_key()
    master_address = cert_instance.get_master_address()

    url = f"https://{master_address}:8140/puppet/v3/environment_classes/"
    data = []
    for environment in environments:
        req = requests.get(
            f"{url}?environment={environment}",
            verify=False,
            cert=(cert_path, private_key_path),
        )
        target = req.json()["files"]
        spec = [
            Coalesce(
                (
                    "classes",
                    [
                        {
                            "name": "name",
                            "params": (
                                "params",
                                [
                                    {
                                        "name": "name",
                                        "type": Coalesce("type", Literal("String")),
                                        "default_source": Coalesce(
                                            "default_source", Literal("")
                                        ),
                                    }
                                ],
                            ),
                            "master": Literal(master_id),
                        }
                    ],
                ),
                Literal([]),
            )
        ]
        for class_data in list(chain(*glom(target, spec))):
            class_data["environment"] = environment
            data.append(class_data)

    user = os.environ.get("WEBAPP_USER", "")
    password = os.environ.get("WEBAPP_PASS", "")
    requests.post(
        "http://webapp:8000/api/classes/sync/", json=data, auth=(user, password)
    )
