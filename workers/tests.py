import json
import unittest
import responses
from jobs.matching_nodes import matching_nodes_sync


def ordered(obj):
    """
    Recursively orders dicts and lists with nested dicts and lists
    """
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    elif isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    return obj


class TestMatchingNodesJob(unittest.TestCase):
    """
    Tests for the job that discover which nodes should
    be in a determined group
    """

    @responses.activate
    def test_only_pinned_nodes(self):
        """
        When the classification rules contain only pinned nodes
        the matching nodes should be the list of pinned nodes
        and a request to the PuppetDB should be avoided
        """
        group_id = "341ff2b4-1e88-40cb-9303-2296d6e55da1"
        master_id = "a3fed008-ad0a-461b-89cf-8aff5fa6b6d6"
        master_address = "10.10.10.10"
        rules_url = f"http://webapp:8000/api/rules/{group_id}/"
        groups_url = f"http://webapp:8000/api/groups/{group_id}/"
        pinned_nodes = ["1234.acme", "puppet-master.example.com.br"]

        responses.add(
            responses.GET,
            rules_url,
            json={"match_type": "ALL", "nodes": pinned_nodes, "facts": []},
            status=200,
        )
        responses.add(responses.PATCH, groups_url, status=200)

        matching_nodes_sync(group_id, master_id, master_address)

        # Two requests: to fetch the rules and update the matching_nodes
        self.assertEqual(2, len(responses.calls))
        # Check if the list sent equals the pinned nodes
        expected_payload = {"matching_nodes": pinned_nodes}
        sent_payload = json.loads(responses.calls[1].request.body)
        self.assertEqual(ordered(expected_payload), ordered(sent_payload))


if __name__ == "__main__":
    unittest.main()
