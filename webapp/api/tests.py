from os import remove
from shutil import copyfile
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files import File
from django.contrib.auth.models import User

from core import models


def ordered(obj):
    """
    Recursively orders dicts and lists with nested dicts and lists
    """
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    elif isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    return obj


class BaseAPITestCase(APITestCase):

    def setUp(self):
        username = "admin"
        password = "admintestpass"
        email = "admin@example.com"
        self.user = User.objects.create_superuser(
            username=username, email=email, password=password
        )
        self.client.login(username=username, password=password)


class ConfigurationTests(BaseAPITestCase):
    """
    Tests to the /configuration endpoint
    """

    def setUp(self):
        super().setUp()
        self.master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        self.environment = models.Environment.objects.create(
            name="production", master_zone=self.master_zone
        )
        self.group = models.Group.objects.create(
            label="grupo01",
            description="Pack my box with five dozen liquor jugs",
            master_zone=self.master_zone,
            environment=self.environment,
        )

    def test_fetch_configuration(self):
        """
        A get request should return all the nested configuration data
        """
        profile_tomcat = models.PuppetClass.objects.create(
            name="profile::tomcat", environment=self.environment
        )
        tomcat_user = models.Parameter.objects.create(
            name="user", puppet_class=profile_tomcat
        )
        tomcat_java_version = models.Parameter.objects.create(
            name="java_version", puppet_class=profile_tomcat
        )
        profile_linux = models.PuppetClass.objects.create(
            name="profile::base::linux", environment=self.environment
        )
        profile_puppet_agent = models.PuppetClass.objects.create(
            name="profile::puppet::agent", environment=self.environment
        )
        profile_puppet_mco = models.PuppetClass.objects.create(
            name="profile::puppet::mcollective", environment=self.environment
        )
        models.ConfigurationClass.objects.create(
            puppet_class=profile_linux, configuration=self.group.configuration
        )
        models.ConfigurationClass.objects.create(
            puppet_class=profile_puppet_agent, configuration=self.group.configuration
        )
        models.ConfigurationClass.objects.create(
            puppet_class=profile_puppet_mco, configuration=self.group.configuration
        )
        tomcat_config = models.ConfigurationClass.objects.create(
            puppet_class=profile_tomcat, configuration=self.group.configuration
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config, parameter=tomcat_user, raw_value="tomcat"
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config,
            parameter=tomcat_java_version,
            raw_value="1.8.0",
        )

        expected_json = {
            "classes": [
                {"puppet_class": profile_linux.name, "parameters": []},
                {"puppet_class": profile_puppet_agent.name, "parameters": []},
                {"puppet_class": profile_puppet_mco.name, "parameters": []},
                {
                    "puppet_class": profile_tomcat.name,
                    "parameters": [
                        {
                            "value": "tomcat",
                            "raw_value": "tomcat",
                            "parameter": tomcat_user.name,
                        },
                        {
                            "value": "1.8.0",
                            "raw_value": "1.8.0",
                            "parameter": tomcat_java_version.name,
                        },
                    ],
                },
            ]
        }
        url = f"/api/configuration/{self.group.id}/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered(response.json()), ordered(expected_json))

    def test_basic_register_configuration(self):
        """
        A put request to the endpoint should update
        all the nested structure of the configuration
        """
        profile_tomcat = models.PuppetClass.objects.create(
            name="profile::tomcat", environment=self.environment
        )
        tomcat_user = models.Parameter.objects.create(
            name="user", puppet_class=profile_tomcat
        )
        tomcat_java_version = models.Parameter.objects.create(
            name="java_version", puppet_class=profile_tomcat
        )

        payload = {
            "classes": [
                {
                    "puppet_class": profile_tomcat.name,
                    "parameters": [
                        {
                            "value": "tomcat",
                            "raw_value": "tomcat",
                            "parameter": tomcat_user.name,
                        },
                        {
                            "value": "1.8.0",
                            "raw_value": "1.8.0",
                            "parameter": tomcat_java_version.name,
                        },
                    ],
                }
            ]
        }
        url = "/api/configuration/" + str(self.group.id) + "/"
        response = self.client.put(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Fetch the config and check if it's equal to the expected
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered(response.json()), ordered(payload))
        # Assert log created with current user
        log = models.UserLog.objects.get(user=self.user, request_method="PUT")
        self.assertIn(url, log.request_path)

    def test_override_configuration(self):
        """
        A put request with a completely different configuration
        should override all the existing configuration
        """
        profile_tomcat = models.PuppetClass.objects.create(
            name="profile::tomcat", environment=self.environment
        )
        tomcat_user = models.Parameter.objects.create(
            name="user", puppet_class=profile_tomcat
        )
        tomcat_java_version = models.Parameter.objects.create(
            name="java_version", puppet_class=profile_tomcat
        )
        profile_linux = models.PuppetClass.objects.create(
            name="profile::base::linux", environment=self.environment
        )
        profile_puppet_agent = models.PuppetClass.objects.create(
            name="profile::puppet::agent", environment=self.environment
        )
        profile_puppet_mco = models.PuppetClass.objects.create(
            name="profile::puppet::mcollective", environment=self.environment
        )
        models.ConfigurationClass.objects.create(
            puppet_class=profile_linux, configuration=self.group.configuration
        )
        models.ConfigurationClass.objects.create(
            puppet_class=profile_puppet_agent, configuration=self.group.configuration
        )

        expected_json = {
            "classes": [
                {"puppet_class": profile_linux.name, "parameters": []},
                {"puppet_class": profile_puppet_agent.name, "parameters": []},
            ]
        }
        url = "/api/configuration/" + str(self.group.id) + "/"
        # Check initial state
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered(response.json()), ordered(expected_json))

        # Updates the configuration
        payload = {
            "classes": [
                {"puppet_class": profile_puppet_agent.name, "parameters": []},
                {"puppet_class": profile_puppet_mco.name, "parameters": []},
                {
                    "puppet_class": profile_tomcat.name,
                    "parameters": [
                        {
                            "value": "tomcat",
                            "raw_value": "tomcat",
                            "parameter": tomcat_user.name,
                        },
                        {
                            "value": "1.8.0",
                            "raw_value": "1.8.0",
                            "parameter": tomcat_java_version.name,
                        },
                    ],
                },
            ]
        }
        response = self.client.put(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Fetch the config and check if it's equal to the expected
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered(response.json()), ordered(payload))
        # Assert log created with current user
        log = models.UserLog.objects.get(user=self.user, request_method="PUT")
        self.assertIn(url, log.request_path)

    def test_override_parameters(self):
        """
        A put request with a completely different configuration
        should override all the existing configuration
        """
        profile_tomcat = models.PuppetClass.objects.create(
            name="profile::tomcat", environment=self.environment
        )
        tomcat_user = models.Parameter.objects.create(
            name="user", puppet_class=profile_tomcat
        )
        tomcat_java_version = models.Parameter.objects.create(
            name="java_version", puppet_class=profile_tomcat
        )
        tomcat_nofile = models.Parameter.objects.create(
            name="nofile", puppet_class=profile_tomcat
        )
        tomcat_config = models.ConfigurationClass.objects.create(
            puppet_class=profile_tomcat, configuration=self.group.configuration
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config, parameter=tomcat_user, raw_value="tomcat"
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config,
            parameter=tomcat_java_version,
            raw_value="1.8.0",
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config, parameter=tomcat_nofile, raw_value="5000"
        )

        expected_json = {
            "classes": [
                {
                    "puppet_class": profile_tomcat.name,
                    "parameters": [
                        {
                            "value": "tomcat",
                            "raw_value": "tomcat",
                            "parameter": tomcat_user.name,
                        },
                        {
                            "value": "1.8.0",
                            "raw_value": "1.8.0",
                            "parameter": tomcat_java_version.name,
                        },
                        {
                            "value": "5000",
                            "raw_value": "5000",
                            "parameter": tomcat_nofile.name,
                        },
                    ],
                }
            ]
        }
        url = "/api/configuration/" + str(self.group.id) + "/"
        # Check initial state
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered(response.json()), ordered(expected_json))

        # Updates the configuration
        payload = {
            "classes": [
                {
                    "puppet_class": profile_tomcat.name,
                    "parameters": [
                        {
                            "value": "1.7.0",
                            "raw_value": "1.7.0",
                            "parameter": tomcat_java_version.name,
                        },
                        {
                            "value": "32000",
                            "raw_value": "32000",
                            "parameter": tomcat_nofile.name,
                        },
                    ],
                }
            ]
        }
        response = self.client.put(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Fetch the config and check if it's equal to the expected
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered(response.json()), ordered(payload))

    def test_duplicate_parameter(self):
        """
        A put request with a completely different configuration
        should override all the existing configuration
        """
        profile_tomcat = models.PuppetClass.objects.create(
            name="profile::tomcat", environment=self.environment
        )
        tomcat_user = models.Parameter.objects.create(
            name="user", puppet_class=profile_tomcat
        )
        tomcat_config = models.ConfigurationClass.objects.create(
            puppet_class=profile_tomcat, configuration=self.group.configuration
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config, parameter=tomcat_user, raw_value="tomcat"
        )
        expected_json = {
            "classes": [
                {
                    "puppet_class": profile_tomcat.name,
                    "parameters": [
                        {
                            "value": "tomcat",
                            "raw_value": "tomcat",
                            "parameter": tomcat_user.name,
                        }
                    ],
                }
            ]
        }
        url = "/api/configuration/" + str(self.group.id) + "/"
        # Check initial state
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered(response.json()), ordered(expected_json))

        # Adds new class same parameter name
        profile_apache = models.PuppetClass.objects.create(
            name="profile::apache", environment=self.environment
        )
        apache_user = models.Parameter.objects.create(
            name="user", puppet_class=profile_apache
        )
        apache_config = models.ConfigurationClass.objects.create(
            puppet_class=profile_apache, configuration=self.group.configuration
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=apache_config, parameter=apache_user, raw_value="apache"
        )

        # Updates the configuration
        payload = {
            "classes": [
                {
                    "puppet_class": profile_tomcat.name,
                    "parameters": [
                        {
                            "value": "testing",
                            "raw_value": "testing",
                            "parameter": tomcat_user.name,
                        }
                    ],
                }
            ]
        }
        response = self.client.put(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_string_type_parameter(self):
        """
        Test if the parameter value is being identified as string correctly
        """
        profile_tomcat = models.PuppetClass.objects.create(
            name="profile::tomcat", environment=self.environment
        )
        tomcat_str = models.Parameter.objects.create(
            name="str", value_type="String", puppet_class=profile_tomcat
        )
        tomcat_config = models.ConfigurationClass.objects.create(
            puppet_class=profile_tomcat, configuration=self.group.configuration
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config,
            parameter=tomcat_str,
            raw_value="loremipsum",
        )
        expected_json = {
            "classes": [
                {
                    "puppet_class": profile_tomcat.name,
                    "parameters": [
                        {
                            "value": "loremipsum",
                            "raw_value": "loremipsum",
                            "parameter": tomcat_str.name,
                        }
                    ],
                }
            ]
        }
        url = "/api/configuration/" + str(self.group.id) + "/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered(response.json()), ordered(expected_json))

    def test_integer_type_parameter(self):
        """
        Test if the parameter value is being converted to int correctly
        """
        profile_tomcat = models.PuppetClass.objects.create(
            name="profile::tomcat", environment=self.environment
        )
        tomcat_number = models.Parameter.objects.create(
            name="number", value_type="Integer", puppet_class=profile_tomcat
        )
        tomcat_config = models.ConfigurationClass.objects.create(
            puppet_class=profile_tomcat, configuration=self.group.configuration
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config, parameter=tomcat_number, raw_value="1"
        )
        expected_json = {
            "classes": [
                {
                    "puppet_class": profile_tomcat.name,
                    "parameters": [
                        {"value": 1, "raw_value": "1", "parameter": tomcat_number.name}
                    ],
                }
            ]
        }
        url = "/api/configuration/" + str(self.group.id) + "/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered(response.json()), ordered(expected_json))

    def test_float_type_parameter(self):
        """
        Test if the parameter value is being converted to float correctly
        """
        profile_tomcat = models.PuppetClass.objects.create(
            name="profile::tomcat", environment=self.environment
        )
        tomcat_number = models.Parameter.objects.create(
            name="number", value_type="Float", puppet_class=profile_tomcat
        )
        tomcat_config = models.ConfigurationClass.objects.create(
            puppet_class=profile_tomcat, configuration=self.group.configuration
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config, parameter=tomcat_number, raw_value="1.1"
        )
        expected_json = {
            "classes": [
                {
                    "puppet_class": profile_tomcat.name,
                    "parameters": [
                        {
                            "value": 1.1,
                            "raw_value": "1.1",
                            "parameter": tomcat_number.name,
                        }
                    ],
                }
            ]
        }
        url = "/api/configuration/" + str(self.group.id) + "/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered(response.json()), ordered(expected_json))

    def test_boolean_type_parameter(self):
        """
        Test if the parameter value is being converted to boolean correctly
        """
        profile_tomcat = models.PuppetClass.objects.create(
            name="profile::tomcat", environment=self.environment
        )
        tomcat_bool = models.Parameter.objects.create(
            name="bool", value_type="Boolean", puppet_class=profile_tomcat
        )
        tomcat_config = models.ConfigurationClass.objects.create(
            puppet_class=profile_tomcat, configuration=self.group.configuration
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config, parameter=tomcat_bool, raw_value="True"
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config, parameter=tomcat_bool, raw_value="False"
        )
        expected_json = {
            "classes": [
                {
                    "puppet_class": profile_tomcat.name,
                    "parameters": [
                        {
                            "value": True,
                            "raw_value": "True",
                            "parameter": tomcat_bool.name,
                        },
                        {
                            "value": False,
                            "raw_value": "False",
                            "parameter": tomcat_bool.name,
                        },
                    ],
                }
            ]
        }
        url = "/api/configuration/" + str(self.group.id) + "/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered(response.json()), ordered(expected_json))

    def test_unusual_type_parameter(self):
        """
        Test if the parameter value is being mantained as text if the type is not identified
        """
        profile_tomcat = models.PuppetClass.objects.create(
            name="profile::tomcat", environment=self.environment
        )
        tomcat_unusual = models.Parameter.objects.create(
            name="unusual", value_type="NotKnown", puppet_class=profile_tomcat
        )
        tomcat_config = models.ConfigurationClass.objects.create(
            puppet_class=profile_tomcat, configuration=self.group.configuration
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config,
            parameter=tomcat_unusual,
            raw_value="loremipsum",
        )
        expected_json = {
            "classes": [
                {
                    "puppet_class": profile_tomcat.name,
                    "parameters": [
                        {
                            "value": "loremipsum",
                            "raw_value": "loremipsum",
                            "parameter": tomcat_unusual.name,
                        }
                    ],
                }
            ]
        }
        url = "/api/configuration/" + str(self.group.id) + "/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered(response.json()), ordered(expected_json))


class RulesTests(BaseAPITestCase):
    """
    Tests to the /rules endpoint
    """

    def test_fetch_rules(self):
        """
        A get request should return all the classification rules
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        group = models.Group.objects.create(
            label="grupo01",
            description="Pack my box with five dozen liquor jugs",
            master_zone=master_zone,
            environment=environment,
        )
        osfamily = models.Fact.objects.create(name="osfamily", master_zone=master_zone)
        node = models.Node.objects.create(certname="1234.acme", master_zone=master_zone)
        rules = models.Rule.objects.get(group=group)
        rules.nodes.set([node])
        rules.facts.create(
            fact=osfamily, operator=models.FactRule.NOT_EQUAL, value="Debian"
        )
        expected_json = {
            "match_type": "ALL",
            "nodes": ["1234.acme"],
            "facts": [{"fact": "osfamily", "operator": "!=", "value": "Debian"}],
        }
        url = "/api/rules/" + str(group.id) + "/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered(response.json()), ordered(expected_json))

    def test_update_match_type(self):
        """
        A put request should update the match_type
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        group = models.Group.objects.create(
            label="grupo01",
            description="Pack my box with five dozen liquor jugs",
            master_zone=master_zone,
            environment=environment,
        )
        osfamily = models.Fact.objects.create(name="osfamily", master_zone=master_zone)
        rules = models.Rule.objects.get(group=group)
        rules.facts.create(fact=osfamily, value="Redhat")
        expected_json = {
            "match_type": "ALL",
            "nodes": [],
            "facts": [{"fact": "osfamily", "operator": "=", "value": "Redhat"}],
        }
        url = "/api/rules/" + str(group.id) + "/"
        # Check initial state
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered(response.json()), ordered(expected_json))

        # Update the rules
        payload = {
            "match_type": "ANY",
            "nodes": [],
            "facts": [{"fact": "osfamily", "operator": "=", "value": "Redhat"}],
        }
        # Mock faktory connection
        with patch("faktory.connection"):
            response = self.client.put(url, data=payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Fetch the rules and check if it's equal to the expected
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered(response.json()), ordered(payload))


class VariablesTests(BaseAPITestCase):
    """
    Tests to the /variables endpoint
    """

    def test_fetch_variables(self):
        """
        A get request should return the variables
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        group = models.Group.objects.create(
            label="grupo01",
            description="Pack my box with five dozen liquor jugs",
            master_zone=master_zone,
            environment=environment,
        )
        variable = models.Variable.objects.get(group=group)
        variable.data = {
            "management_type": "GT",
            "special_customer": "no",
            "another-one": "bites-the-dust",
        }
        variable.save()
        expected_json = {
            "data": {
                "management_type": "GT",
                "special_customer": "no",
                "another-one": "bites-the-dust",
            }
        }
        url = "/api/variables/" + str(group.id) + "/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ordered(response.json()), ordered(expected_json))

    def test_update_variables(self):
        """
        A put request should update variables definition
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        group = models.Group.objects.create(
            label="grupo01",
            description="Pack my box with five dozen liquor jugs",
            master_zone=master_zone,
            environment=environment,
        )
        variable = models.Variable.objects.get(group=group)
        variable.data = {
            "management_type": "GT",
            "special_customer": "no",
            "another-one": "bites-the-dust",
        }
        variable.save()
        # Update the variables
        payload = {"data": {"management_type": "SG", "secret": "mystery"}}
        url = "/api/variables/" + str(group.id) + "/"
        response = self.client.put(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if the variables were updated
        response = self.client.get(url, format="json")
        self.assertEqual(ordered(response.json()), ordered(payload))


class PuppetClassesTests(BaseAPITestCase):
    """
    Tests to the /classes endpoint
    """

    def test_sync_classes(self):
        """
        Test a class sync through a endpoint post
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        payload = [
            {
                "name": "activemq::service",
                "params": [
                    {"name": "ensure", "type": "String", "default_source": ""},
                    {"name": "service_enable", "type": "String", "default_source": ""},
                ],
                "master": master_zone.pk,
                "environment": environment.name,
            },
            {
                "name": "activemq::ssl",
                "params": [
                    {
                        "name": "truststore_password",
                        "type": "String",
                        "default_source": "",
                    },
                    {
                        "name": "keystore_password",
                        "type": "String",
                        "default_source": "",
                    },
                ],
                "master": master_zone.pk,
                "environment": environment.name,
            },
        ]
        url = "/api/classes/sync/"
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        class_names = models.PuppetClass.objects.filter(
            environment=environment
        ).values_list("name", flat=True)
        self.assertIn("activemq::service", class_names)
        self.assertIn("activemq::ssl", class_names)

        activemq_service_params = models.Parameter.objects.filter(
            puppet_class__name="activemq::service"
        ).values_list("name", flat=True)
        self.assertIn("ensure", activemq_service_params)
        self.assertIn("service_enable", activemq_service_params)

        activemq_ssl_params = models.Parameter.objects.filter(
            puppet_class__name="activemq::ssl"
        ).values_list("name", flat=True)
        self.assertIn("keystore_password", activemq_ssl_params)
        self.assertIn("truststore_password", activemq_ssl_params)

    def test_sync_classes_with_complex_params(self):
        """
        Test a class (with complex params) sync through a endpoint post
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        payload = [
            {
                "name": "someclass::with_complex_params",
                "params": [
                    {
                        "name": "enum",
                        "type": 'Enum["Option1", "Option2"]',
                        "default_source": "Option1",
                    },
                    {
                        "name": "optional",
                        "type": "Optional[String]",
                        "default_source": "str",
                    },
                ],
                "master": master_zone.pk,
                "environment": environment.name,
            }
        ]
        url = "/api/classes/sync/"
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        class_names = models.PuppetClass.objects.filter(
            environment=environment
        ).values_list("name", flat=True)
        self.assertIn("someclass::with_complex_params", class_names)

        expected_params = [
            {
                "name": "enum",
                "value_type": "Enum",
                "value_default": "Option1",
                "values": '"Option1", "Option2"',
            },
            {
                "name": "optional",
                "value_type": "Optional",
                "value_default": "str",
                "values": "String",
            },
        ]
        saved_params = list(
            models.Parameter.objects.filter(
                puppet_class__name="someclass::with_complex_params"
            ).values("name", "value_type", "value_default", "values")
        )
        self.assertEqual(ordered(expected_params), ordered(saved_params))

    def test_sync_classes_with_existing_params(self):
        """
        Test a class (with already created params) sync through a endpoint post
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        # Create PuppetClass catalog::product::mysql::master
        mysql_class = models.PuppetClass.objects.create(
            name="catalog::product::mysql::master", environment=environment
        )
        # Create mysql parameter root_password, with type Optional
        models.Parameter.objects.create(
            name="root_password",
            puppet_class=mysql_class,
            value_default="undef",
            value_type="Optional",
            values="String",
        )
        payload = [
            {
                "name": "catalog::product::mysql::master",
                "params": [
                    {
                        "name": "root_password",
                        "type": "Optional[String]",
                        "default_source": "undef",
                    },
                    {"name": "users", "type": "Hash", "default_source": "{ }"},
                ],
                "master": master_zone.pk,
                "environment": environment.name,
            }
        ]
        url = "/api/classes/sync/"
        response = self.client.post(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert only one "root_password" registered
        self.assertEqual(
            models.Parameter.objects.filter(name="root_password").count(), 1
        )


class GroupsTests(BaseAPITestCase):
    """
    Tests to the /groups endpoint
    """

    def test_new_group(self):
        """
        Tests a group creation
        """
        group_query = models.Group.objects.filter(label="label1")
        self.assertEqual(group_query.count(), 0)

        master_zone = models.MasterZone.objects.create(
            label="Master1", address="http://0.0.0.0"
        )
        models.Environment.objects.create(name="production", master_zone=master_zone)
        data = {
            "description": "description1",
            "label": "label1",
            "master_zone": master_zone.id,
            "tags_list": ["tag1", "tag2"],
        }
        url = "/api/groups/"
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        group = models.Group.objects.filter(label="label1")[0]
        self.assertEqual(group.description, "description1")
        self.assertEqual(group.tags_list, ["tag1", "tag2"])
        self.assertEqual(group.master_zone.id, master_zone.id)

    def test_update_matching_nodes(self):
        """
        Tests a matching_nodes field update
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        group = models.Group.objects.create(
            label="grupo01",
            description="Pack my box with five dozen liquor jugs",
            master_zone=master_zone,
            environment=environment,
        )
        master_zone.nodes.create(certname="1234.acme")
        master_zone.nodes.create(certname="555.contoso")
        master_zone.nodes.create(certname="888.empresa")
        payload = {"matching_nodes": ["555.contoso"]}
        url = "/api/groups/" + str(group.id) + "/"
        response = self.client.patch(url, data=payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        group.refresh_from_db()
        nodes = group.matching_nodes.values_list("certname", flat=True)
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0], "555.contoso")


class NodesTests(BaseAPITestCase):
    """
    Tests to the /nodes endpoint
    """

    def test_node_sync(self):
        """
        Should sync list of nodes
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        data = [
            {"certname": "1234.acme", "master_zone": master_zone.id},
            {"certname": "888.empresa", "master_zone": master_zone.id},
            {"certname": "555.contoso", "master_zone": master_zone.id},
        ]
        url = "/api/nodes/sync/"
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assert nodes created
        self.assertEqual(models.Node.objects.count(), 3)

    def test_node_sync_update(self):
        """
        Should sync list of nodes, and ignore existing nodes
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        # Create existing node
        models.Node.objects.create(certname="1234.acme", master_zone=master_zone)
        # Try to save it again
        data = [
            {"certname": "1234.acme", "master_zone": master_zone.id},
            {"certname": "888.empresa", "master_zone": master_zone.id},
            {"certname": "555.contoso", "master_zone": master_zone.id},
        ]
        url = "/api/nodes/sync/"
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assert nodes created
        self.assertEqual(models.Node.objects.count(), 3)

    def test_node_classifier_string_params(self):
        """
        A get request should return the ENC yaml file
        endpoint receives string parameters certname and master_id
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        node = models.Node.objects.create(certname="1234.acme", master_zone=master_zone)
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        group1 = models.Group.objects.create(
            label="grupo01",
            description="Group number 1",
            master_zone=master_zone,
            environment=environment,
        )
        group1.matching_nodes.set([node])
        group2 = models.Group.objects.create(
            label="grupo02",
            description="Group number 2",
            master_zone=master_zone,
            environment=environment,
        )
        group2.matching_nodes.set([node])
        # Add variables to groups
        variable = models.Variable.objects.get(group=group1)
        variable.data = {"special_customer": False, "random": [1, 2]}
        variable.save()
        variable = models.Variable.objects.get(group=group2)
        variable.data = {"management_type": "GT"}
        variable.save()

        profile_tomcat = models.PuppetClass.objects.create(
            name="profile::tomcat", environment=environment
        )
        tomcat_user = models.Parameter.objects.create(
            name="user", puppet_class=profile_tomcat
        )
        tomcat_java_version = models.Parameter.objects.create(
            name="java_version", puppet_class=profile_tomcat
        )
        profile_linux = models.PuppetClass.objects.create(
            name="profile::base::linux", environment=environment
        )
        profile_puppet_agent = models.PuppetClass.objects.create(
            name="profile::puppet::agent", environment=environment
        )
        models.Parameter.objects.create(
            name="version", puppet_class=profile_puppet_agent
        )
        profile_puppet_mco = models.PuppetClass.objects.create(
            name="profile::puppet::mcollective", environment=environment
        )
        models.ConfigurationClass.objects.create(
            puppet_class=profile_linux, configuration=group1.configuration
        )
        models.ConfigurationClass.objects.create(
            puppet_class=profile_puppet_agent, configuration=group1.configuration
        )
        models.ConfigurationClass.objects.create(
            puppet_class=profile_puppet_mco, configuration=group2.configuration
        )
        tomcat_config = models.ConfigurationClass.objects.create(
            puppet_class=profile_tomcat, configuration=group2.configuration
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config, parameter=tomcat_user, raw_value="tomcat"
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config,
            parameter=tomcat_java_version,
            raw_value="1.8.0",
        )
        url = "/api/nodes/node_classifier/?certname=%s&master_id=%s" % (
            node.certname,
            master_zone.id,
        )
        response = self.client.get(url)
        expected_yaml = (
            "classes:\n"
            "  profile::base::linux:\n"
            "  profile::puppet::agent:\n"
            "  profile::puppet::mcollective:\n"
            "  profile::tomcat:\n"
            "    java_version: 1.8.0\n"
            "    user: tomcat\n"
            "environment: production\n"
            "parameters:\n"
            "  management_type: GT\n"
            "  random: '[1, 2]'\n"
            "  special_customer: 'False'\n"
        )
        self.assertEqual(response.content.decode("utf-8"), expected_yaml)

    def test_node_classifier_non_string_params(self):
        """
        A get request should return the ENC yaml file
        endpoint receives string parameters certname and master_id
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        node = models.Node.objects.create(certname="1234.acme", master_zone=master_zone)
        group1 = models.Group.objects.create(
            label="grupo01",
            description="Group number 1",
            master_zone=master_zone,
            environment=environment,
        )
        group1.matching_nodes.set([node])
        group2 = models.Group.objects.create(
            label="grupo02",
            description="Group number 2",
            master_zone=master_zone,
            environment=environment,
        )
        group2.matching_nodes.set([node])
        # Add variables to groups
        variable = models.Variable.objects.get(group=group1)
        variable.data = {"special_customer": False, "random": [1, 2]}
        variable.save()
        variable = models.Variable.objects.get(group=group2)
        variable.data = {"management_type": "GT"}
        variable.save()

        profile_tomcat = models.PuppetClass.objects.create(
            name="profile::tomcat", environment=environment
        )
        param_int = models.Parameter.objects.create(
            name="int", value_type="Integer", puppet_class=profile_tomcat
        )
        param_float = models.Parameter.objects.create(
            name="float", value_type="Float", puppet_class=profile_tomcat
        )
        param_bool = models.Parameter.objects.create(
            name="bool", value_type="Boolean", puppet_class=profile_tomcat
        )
        param_array = models.Parameter.objects.create(
            name="array", value_type="Array", puppet_class=profile_tomcat
        )
        param_hash = models.Parameter.objects.create(
            name="hash", value_type="Hash", puppet_class=profile_tomcat
        )

        tomcat_config = models.ConfigurationClass.objects.create(
            puppet_class=profile_tomcat, configuration=group2.configuration
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config, parameter=param_int, raw_value="123"
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config, parameter=param_bool, raw_value="True"
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config, parameter=param_float, raw_value="0.1"
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config,
            parameter=param_array,
            raw_value="['a.st1.ntp.br', 'a.ntp.br']",
        )
        models.ConfigurationParameter.objects.create(
            configuration_class=tomcat_config,
            parameter=param_hash,
            raw_value=r"{'db1': {'charset': 'utf8', 'name': 'db1'}, 'db2': {'charset': 'utf8', 'name': 'db2'}}",
        )
        url = "/api/nodes/node_classifier/?certname=%s&master_id=%s" % (
            node.certname,
            master_zone.id,
        )
        response = self.client.get(url)
        expected_yaml = (
            "classes:\n"
            "  profile::tomcat:\n"
            "    array:\n"
            "    - a.st1.ntp.br\n"
            "    - a.ntp.br\n"
            "    bool: true\n"
            "    float: 0.1\n"
            "    hash:\n"
            "      db1:\n"
            "        charset: utf8\n"
            "        name: db1\n"
            "      db2:\n"
            "        charset: utf8\n"
            "        name: db2\n"
            "    int: 123\n"
            "environment: production\n"
            "parameters:\n"
            "  management_type: GT\n"
            "  random: '[1, 2]'\n"
            "  special_customer: 'False'\n"
        )
        self.assertEqual(response.content.decode("utf-8"), expected_yaml)

    def test_empty_node(self):
        """
        A request of classification data to a node without classification
        settings should return an empty yaml
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        node = models.Node.objects.create(certname="1234.acme", master_zone=master_zone)

        url = "/api/nodes/node_classifier/?certname=%s&master_id=%s" % (
            node.certname,
            master_zone.id,
        )
        response = self.client.get(url)
        expected_yaml = "classes:\n" "environment: production\n" "parameters:\n"
        self.assertEqual(response.content.decode("utf-8"), expected_yaml)

    def test_nonexistent_node(self):
        """
        A request of classification data to a nonexistent node
        should return an empty yaml
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )

        url = "/api/nodes/node_classifier/?certname=%s&master_id=%s" % (
            "desconhecido.example.net.br",
            master_zone.id,
        )
        response = self.client.get(url)
        expected_yaml = "classes:\n" "environment: production\n" "parameters:\n"
        self.assertEqual(response.content.decode("utf-8"), expected_yaml)

    def test_node_classifier_no_params(self):
        """
        Assert error message when endpoint called without parameters
        """
        url = "/api/nodes/node_classifier/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_json = {"error": "Invalid certname or master_id parameters"}
        self.assertEqual(response.json(), expected_json)

    def test_node_classifier_wrong_node(self):
        """
        Assert error message when endpoint called with non-existing node
        """
        url = "/api/nodes/node_classifier/?certname=wrong&master_id=fake"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_json = {"error": "Invalid certname or master_id parameters"}
        self.assertEqual(response.json(), expected_json)

    def test_node_classifier_wrong_master(self):
        """
        Assert error message when endpoint called with non-existing master
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        node = models.Node.objects.create(certname="1234.acme", master_zone=master_zone)
        url = (
            "/api/nodes/node_classifier/?certname=%s&master_id=wrong" % node.certname
        )  # noqa
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_json = {"error": "Invalid certname or master_id parameters"}
        self.assertEqual(response.json(), expected_json)


class FactTests(BaseAPITestCase):
    """
    Tests to the /facts endpoint
    """

    def test_fact_sync(self):
        """
        Should sync list of facts
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        data = [
            {"name": "fact1", "master_zone": master_zone.id},
            {"name": "fact2", "master_zone": master_zone.id},
            {"name": "fact3", "master_zone": master_zone.id},
        ]
        url = "/api/facts/sync/"
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assert facts created
        self.assertEqual(models.Fact.objects.count(), 3)

    def test_fact_sync_update(self):
        """
        Should sync list of facts, and ignore existing facts
        """
        master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        # Create existing fact
        models.Fact.objects.create(name="fact1", master_zone=master_zone)
        # Try to save it again
        data = [
            {"name": "fact1", "master_zone": master_zone.id},
            {"name": "fact2", "master_zone": master_zone.id},
            {"name": "fact3", "master_zone": master_zone.id},
        ]
        url = "/api/facts/sync/"
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assert facts created
        self.assertEqual(models.Fact.objects.count(), 3)


class MasterZoneTests(BaseAPITestCase):
    """
    Tests to the /master_zones endpoint
    """

    def test_forbidden_request(self):
        """
        Test unauthenticated users and users without permission
        """
        # Test authenticated superuser
        url = f"/api/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Test unauthenticated user
        self.client.logout()
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Test unauthorized user
        username = "user1"
        password = "user1pass"
        email = "user1@example.com"
        User.objects.create_user(username=username, email=email, password=password)
        self.client.login(username=username, password=password)
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_master_get(self):
        """
        A GET request to the master should return urls with the
        master cert files
        """
        # Copy dummy certs from /certs to /code
        # Trying to load directly from /certs
        # raise a django.core.exceptions.SuspiciousFileOperation
        certname = "puppet-grua.example.com.pem"
        tmp_cert = f"/code/uploads/cert_{certname}"
        tmp_pk = f"/code/uploads/pk_{certname}"
        copyfile(f"/code/dummy_certs/cert/{certname}", tmp_cert)
        copyfile(f"/code/dummy_certs/private_keys/{certname}", tmp_pk)
        cert = open(tmp_cert)
        private_key = open(tmp_pk)
        # Create the master
        master_zone = models.MasterZone.objects.create(
            label="Splinter",
            address="http://10.10.10.10",
            signed_cert=File(cert),
            private_key=File(private_key),
        )
        # Close the files
        cert.close()
        private_key.close()
        # Remove the copied certs
        remove(tmp_cert)
        remove(tmp_pk)
        url = f"/api/master_zones/{master_zone.pk}/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertIsInstance(response_json["signed_cert"], str)
        self.assertIsInstance(response_json["private_key"], str)
        # Should be URLs
        self.assertIn("http://", response_json["signed_cert"])
        self.assertIn("http://", response_json["private_key"])
        # Remove the uploaded certs
        remove(master_zone.signed_cert.path)
        remove(master_zone.private_key.path)

    def test_register_master(self):
        """
        A POST request to the masters endpoint should register
        a new master and upload the cert files
        """
        # Copy dummy certs from /certs to /code
        # Trying to load directly from /certs
        # raise a django.core.exceptions.SuspiciousFileOperation
        cert = open("/code/dummy_certs/cert/puppet-grua.example.com.pem")
        private_key = open("/code/dummy_certs/cert/puppet-grua.example.com.pem")
        data = {
            "label": "Splinter",
            "address": "http://10.10.10.10",
            "signed_cert": cert,
            "private_key": private_key,
        }
        url = "/api/master_zones/"
        response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_json = response.json()
        # Check uploaded files
        self.assertIsInstance(response_json["signed_cert"], str)
        self.assertIsInstance(response_json["private_key"], str)
        # Should be URLs
        self.assertIn("http://", response_json["signed_cert"])
        self.assertIn("http://", response_json["private_key"])
        master_zone = models.MasterZone.objects.get()
        # Remove the uploaded certs
        remove(master_zone.signed_cert.path)
        remove(master_zone.private_key.path)

        def test_environments_sync(self):
            """
            A POST request to the master_zone environments_sync endpoint
            should sync the master_zone environments
            """
            master_zone = models.MasterZone.objects.create(
                label="Master", address="0.0.0.0"
            )
            environments = ["production", "homol", "test"]
            data = {"master_id": master_zone.id, "environments": environments}
            url = "/api/master_zones/environments_sync/"
            response = self.client.post(url, data=data, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            master_zone.refresh_from_db()
            saved_environments = list(
                master_zone.environments.all().values_list("name", flat=True)
            )
            self.assertListEqual(environments, saved_environments)


class ParameterTests(BaseAPITestCase):
    """
    Tests to the /parameter endpoint
    """

    def setUp(self):
        super().setUp()
        self.master_zone = models.MasterZone.objects.create(
            label="Splinter", address="http://10.10.10.10"
        )
        self.environment = models.Environment.objects.create(
            name="production", master_zone=self.master_zone
        )

    def test_parameter_without_values(self):
        """
        Test the parameter endpoint passing a parameter without values
        """
        puppet_class = models.PuppetClass.objects.create(
            name="class", environment=self.environment
        )
        parameter = models.Parameter.objects.create(
            name="bool",
            value_type="Boolean",
            value_default="True",
            puppet_class=puppet_class,
        )
        expected_json = {
            "id": str(parameter.id),
            "name": "bool",
            "puppet_class": str(puppet_class.id),
            "type": "Boolean",
            "default": "True",
            "values": ["True", "False"],
        }
        url = "/api/parameters/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json()[0], expected_json)

    def test_parameter_with_values(self):
        """
        Test the parameter endpoint passing a parameter with values
        """
        puppet_class = models.PuppetClass.objects.create(
            name="class", environment=self.environment
        )
        parameter = models.Parameter.objects.create(
            name="enum",
            value_type='Enum["Option1", "Option2"]',
            value_default="Option1",
            puppet_class=puppet_class,
        )
        expected_json = {
            "id": str(parameter.id),
            "name": "enum",
            "puppet_class": str(puppet_class.id),
            "type": "Enum",
            "default": "Option1",
            "values": ["Option1", "Option2"],
        }
        url = "/api/parameters/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json()[0], expected_json)
