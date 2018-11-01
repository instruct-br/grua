from django.test import TestCase
from django.contrib.auth.models import User
from datetime import datetime
from core import models
from guardian.shortcuts import assign_perm


class FrontendTestCase(TestCase):
    """
    Tests for the frontend app views
    """

    def setUp(self):
        """
        Create and authenticate user
        """
        username = "admin"
        password = "admintestpass"
        email = "admin@example.com"
        self.user = User.objects.create_user(
            username=username, email=email, password=password
        )
        self.client.login(username=username, password=password)

    def test_master_zone_list_view(self):
        """
        Test MaterZoneListView
        """
        url = "/master_zones/"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "master_zones/index.html")

    def test_master_zone_create_view(self):
        """
        Test MasterZoneCreate
        """
        url = "/master_zones/new/"
        data = {"label": "MasterZone1", "address": "0.0.0.0"}
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "master_zones/index.html")
        # Assert log created
        log = models.UserLog.objects.get(user=self.user, request_method="POST")
        self.assertIn(url, log.request_path)

    def test_master_zone_update_view(self):
        """
        Test MasterZoneEdit
        """
        master_zone = models.MasterZone.objects.create(
            label="MasterZone1", address="0.0.0.0"
        )
        url = "/master_zones/edit/%s" % master_zone.id
        # Assert user can't update Zone without permission
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        # Give permission for user to access Zone1
        assign_perm("core.has_access", self.user, master_zone)
        # Test Zone update view
        data = {"label": "EditedZone1", "address": "1.2.3.4"}
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "master_zones/index.html")
        # Assert log created
        log = models.UserLog.objects.get(user=self.user, request_method="POST")
        self.assertIn(url, log.request_path)

    def test_master_zone_delete_view(self):
        """
        Test MasterZoneDelete
        """
        master_zone = models.MasterZone.objects.create(
            label="MasterZone1", address="0.0.0.0"
        )
        # Give permission for user to access Zone1
        assign_perm("core.has_access", self.user, master_zone)
        url = "/master_zones/delete/%s" % master_zone.id
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "master_zones/index.html")
        # Assert log created
        log = models.UserLog.objects.get(user=self.user, request_method="POST")
        self.assertIn(url, log.request_path)

    def test_log_list_view(self):
        """
        Test UserLogListView
        """
        # Change user to admin
        self.user.is_superuser = True
        self.user.save()
        # Create some logs
        log1 = models.UserLog.objects.create(
            user=self.user,
            request_path="/master_zones/new/",
            request_method="POST",
            response_code="302",
            datetime=datetime(2018, 6, 1, 10, 0),
        )
        log2 = models.UserLog.objects.create(
            user=self.user,
            request_path="/api/groups/",
            request_method="PUT",
            response_code="302",
            datetime=datetime(2018, 6, 2, 10, 0),
        )
        log3 = models.UserLog.objects.create(
            user=self.user,
            request_path="/master_zones/new/",
            request_method="POST",
            response_code="302",
            datetime=datetime(2018, 6, 3, 10, 0),
        )
        url = "/logs/"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "logs.html")
        # Assert objects in response in the right order
        self.assertEqual(list(response.context["page_obj"]), [log3, log2, log1])

    def test_group_list_view(self):
        """
        Test GroupListView
        """
        # Create groups
        master_zone = models.MasterZone.objects.create(
            label="MasterZone1", address="0.0.0.0"
        )
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        models.Group.objects.create(
            label="Group1",
            description="Group number one",
            master_zone=master_zone,
            environment=environment,
        )
        models.Group.objects.create(
            label="Group2",
            description="Group number two",
            master_zone=master_zone,
            environment=environment,
        )
        url = "/groups/"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "groups/index.html")
        # Assert user won't see Groups he's not permitted
        self.assertListEqual(list(response.context["page_obj"]), [])

    def test_group_list_view_tag_filter(self):
        """
        Test GroupListView filtering by tags
        """
        # Create groups
        master_zone = models.MasterZone.objects.create(
            label="MasterZone1", address="0.0.0.0"
        )
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        # Give permission for user to access Zone1
        assign_perm("core.has_access", self.user, master_zone)
        group1 = models.Group.objects.create(
            label="Group1",
            description="Group number one",
            master_zone=master_zone,
            environment=environment,
        )
        group2 = models.Group.objects.create(
            label="Group2",
            description="Group number two",
            master_zone=master_zone,
            environment=environment,
        )
        # Create tags
        group1.tags.add("tag1", "tag2")
        group2.tags.add("tag1", "tag3")
        # Filter by tag1
        url = "/groups/"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "groups/index.html")
        # Assert all groups returned
        self.assertListEqual(list(response.context["page_obj"]), [group1, group2])
        # Filter by tag2

        data = {"tags": "tag2"}
        url = "/groups/"
        response = self.client.post(url, data=data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "groups/index.html")
        # Assert only one group returned
        self.assertListEqual(list(response.context["page_obj"]), [group1])

    def test_group_list_view_label_filter(self):
        """
        Test GroupListView filtering by label
        """
        # Create groups
        master_zone = models.MasterZone.objects.create(
            label="MasterZone1", address="0.0.0.0"
        )
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        # Give permission for user to access Zone1
        assign_perm("core.has_access", self.user, master_zone)
        environment, _ = models.Environment.objects.get_or_create(name="production")
        group1 = models.Group.objects.create(
            label="Group1",
            description="Group number one",
            master_zone=master_zone,
            environment=environment,
        )
        group2 = models.Group.objects.create(
            label="Group2",
            description="Group number two",
            master_zone=master_zone,
            environment=environment,
        )

        url = "/groups/"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "groups/index.html")
        # Assert all groups returned
        self.assertListEqual(list(response.context["page_obj"]), [group1, group2])

        # Filter by label
        data = {"label": "Group1"}
        url = "/groups/"
        response = self.client.post(url, data=data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "groups/index.html")
        # Assert only one group returned
        self.assertListEqual(list(response.context["page_obj"]), [group1])

    def test_group_list_view_description_filter(self):
        """
        Test GroupListView filtering by label
        """
        # Create groups
        master_zone = models.MasterZone.objects.create(
            label="MasterZone1", address="0.0.0.0"
        )
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        # Give permission for user to access Zone1
        assign_perm("core.has_access", self.user, master_zone)
        environment, _ = models.Environment.objects.get_or_create(name="production")
        group1 = models.Group.objects.create(
            label="Group1",
            description="Group number one",
            master_zone=master_zone,
            environment=environment,
        )
        group2 = models.Group.objects.create(
            label="Group2",
            description="Group number two",
            master_zone=master_zone,
            environment=environment,
        )

        url = "/groups/"
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "groups/index.html")
        # Assert all groups returned
        self.assertListEqual(list(response.context["page_obj"]), [group1, group2])

        # Filter by label
        data = {"description": "two"}
        url = "/groups/"
        response = self.client.post(url, data=data, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "groups/index.html")
        # Assert only one group returned
        self.assertListEqual(list(response.context["page_obj"]), [group2])

    def test_group_create_view(self):
        """
        Test GroupCreate
        """
        url = "/groups/new/"
        master_zone = models.MasterZone.objects.create(
            label="MasterZone1", address="0.0.0.0"
        )
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        # Give permission for user to access Zone1
        assign_perm("core.has_access", self.user, master_zone)
        data = {
            "label": "Group1",
            "master_zone": master_zone.id,
            "environment": environment.id,
            "description": "Group description",
            "tags": "Tag1,Tag2,Tag3",
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "groups/index.html")
        # Assert group created with tags
        self.assertTrue(
            models.Group.objects.filter(
                label="Group1", tags__name__in=["Tag1", "Tag2", "Tag3"]
            ).exists()
        )

    def test_group_update_view(self):
        """
        Test GroupEdit
        """
        master_zone = models.MasterZone.objects.create(
            label="MasterZone1", address="0.0.0.0"
        )
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        # Give permission for user to access Zone1
        assign_perm("core.has_access", self.user, master_zone)
        group = models.Group.objects.create(
            label="Group1",
            description="Group number one",
            master_zone=master_zone,
            environment=environment,
        )
        url = "/groups/edit/%s" % group.id
        data = {
            "label": "Group1",
            "master_zone": master_zone.id,
            "environment": environment.id,
            "description": "Group description",
            "tags": "Tag1,Tag2,Tag3",
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "groups/index.html")
        # Assert group updated with tags
        self.assertTrue(
            models.Group.objects.filter(
                label="Group1", tags__name__in=["Tag1", "Tag2", "Tag3"]
            ).exists()
        )

    def test_group_delete_view(self):
        """
        Test GroupDelete
        """
        master_zone = models.MasterZone.objects.create(
            label="MasterZone1", address="0.0.0.0"
        )
        environment = models.Environment.objects.create(
            name="production", master_zone=master_zone
        )
        # Give permission for user to access Zone1
        assign_perm("core.has_access", self.user, master_zone)
        group = models.Group.objects.create(
            label="Group1",
            description="Group number one",
            master_zone=master_zone,
            environment=environment,
        )
        url = "/groups/delete/%s" % group.id
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "groups/index.html")
        # Assert group deleted
        self.assertFalse(models.Group.objects.filter(label="Group1").exists())
