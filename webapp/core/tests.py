from django.test import TestCase

from core import models


class GroupTests(TestCase):
    """
    Testes for the Group model
    """

    def test_group_create(self):
        """
        When a Group is created, a Configuration, a Rule and a Variable should
        be created too, and they all must share the same UUID
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
        self.assertEqual(models.Configuration.objects.filter(group=group).count(), 1)
        self.assertEqual(models.Rule.objects.filter(group=group).count(), 1)
        self.assertEqual(models.Variable.objects.filter(group=group).count(), 1)
        rule = models.Rule.objects.get(group=group)
        configuration = models.Configuration.objects.get(group=group)
        variable = models.Variable.objects.get(group=group)
        self.assertEqual(group.pk, rule.pk)
        self.assertEqual(group.pk, configuration.pk)
        self.assertEqual(group.pk, variable.pk)
