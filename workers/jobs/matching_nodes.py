import os
import requests
from common import CertsClass
from pypuppetdb.QueryBuilder import (
    AndOperator,
    OrOperator,
    NotOperator,
    EqualsOperator,
    RegexOperator,
    GreaterOperator,
    GreaterEqualOperator,
    LessOperator,
    LessEqualOperator,
)


def _puppetdb_nodes(rules, master_id, master_address):
    if "facts" not in rules or not rules["facts"]:
        return set()

    if rules["match_type"] == "ALL":
        operator = AndOperator()
    else:
        operator = OrOperator()
    for fact_rule in rules["facts"]:
        rule_op = fact_rule["operator"]
        lhs = ["fact", fact_rule["fact"]]
        rhs = fact_rule["value"]
        if rule_op == "=":
            operator.add(EqualsOperator(lhs, rhs))
        elif rule_op == "!=":
            notop = NotOperator()
            notop.add(EqualsOperator(lhs, rhs))
            operator.add(notop)
        elif rule_op == "~":
            operator.add(RegexOperator(lhs, rhs))
        elif rule_op == "!~":
            notop = NotOperator()
            notop.add(RegexOperator(lhs, rhs))
            operator.add(notop)
        elif rule_op == ">":
            operator.add(GreaterOperator(lhs, rhs))
        elif rule_op == ">=":
            operator.add(GreaterEqualOperator(lhs, rhs))
        elif rule_op == "<":
            operator.add(LessOperator(lhs, rhs))
        elif rule_op == "<=":
            operator.add(LessEqualOperator(lhs, rhs))

    query_str = str(operator).replace("'", '"')

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
        nodes_uri = f"https://{master_address}:8081/v4/nodes?query={query_str}"
    else:
        # PuppetDB >= 3.x
        nodes_uri = (
            f"https://{master_address}:8081/pdb/query/v4/nodes?query={query_str}"
        )
    # Fetch the matching nodes
    req = requests.get(nodes_uri, verify=False, cert=(cert_path, private_key_path))
    return {node["certname"] for node in req.json()}


def matching_nodes_sync(group_id, master_id, master_address):
    user = os.environ.get("WEBAPP_USER", "")
    password = os.environ.get("WEBAPP_PASS", "")

    req = requests.get(
        "http://webapp:8000/api/rules/" + group_id + "/", auth=(user, password)
    )
    rules = req.json()

    rules_certnames = _puppetdb_nodes(rules, master_id, master_address)
    pinned_certnames = set(rules["nodes"])

    all_certnames = rules_certnames | pinned_certnames

    # Update the maching nodes
    payload = {"matching_nodes": list(all_certnames)}
    requests.patch(
        "http://webapp:8000/api/groups/" + group_id + "/",
        json=payload,
        auth=(user, password),
    )
