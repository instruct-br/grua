from django.db.models import TextField
from django.test import TestCase

from core import models
from model_bakery import baker


class GroupTests(TestCase):
    """
    Tests for the Group model
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


class ConfigurationParameterTests(TestCase):
    """
    Tests for ConfigurationParameter Model.
    """

    def test_string_value(self):
        """
        string_value should be a text field.
        """
        field = models.ConfigurationParameter._meta.get_field("string_value")
        self.assertIsInstance(field, TextField)

    def test_configurationparameter_save_parameter_string(self):
        """
        Should save raw_value in the string_value field
        if Parameter's value_type field is a string.
        """

        parameter_string = baker.make(
            models.Parameter,
            value_type=models.Parameter.STRING
        )

        configuration_parameter_string = baker.make(
            models.ConfigurationParameter,
            raw_value="test",
            parameter=parameter_string
        )

        self.assertEqual("test", configuration_parameter_string.string_value)

    def test_configurationparameter_save_parameter_integer(self):
        """
        Should save raw_value in the integer_value field
        if Parameter's value_type field is a integer.
        """

        parameter_integer = baker.make(
            models.Parameter,
            value_type=models.Parameter.INTEGER
        )

        configuration_parameter_integer = baker.make(
            models.ConfigurationParameter,
            raw_value=123,
            parameter=parameter_integer
        )

        self.assertEqual(123, configuration_parameter_integer.integer_value)

    def test_configurationparameter_save_parameter_float(self):
        """
        Should save raw_value in the float_value field
        if Parameter's value_type field is a float.
        """

        parameter_float = baker.make(
            models.Parameter,
            value_type=models.Parameter.FLOAT
        )

        configuration_parameter_float = baker.make(
            models.ConfigurationParameter,
            raw_value=9.5,
            parameter=parameter_float
        )

        self.assertEqual(9.5, configuration_parameter_float.float_value)

    def test_configurationparameter_save_parameter_boolean(self):
        """
        Should save raw_value in the boolean_value field
        if Parameter's value_type field is a boolean. 
        
        raw_value must be a string.

        Accepted strings:
            - True = y, yes, t, true, on, 1
            - False = n, no, f, false, off, 0
        """

        parameter_boolean = baker.make(
            models.Parameter,
            value_type=models.Parameter.BOOLEAN
        )

        configuration_parameter_boolean_false = baker.make(
            models.ConfigurationParameter,
            raw_value="False",
            parameter=parameter_boolean
        )

        self.assertEqual(False, configuration_parameter_boolean_false.boolean_value)

        configuration_parameter_boolean_true = baker.make(
            models.ConfigurationParameter,
            raw_value="True",
            parameter=parameter_boolean
        )

        self.assertEqual(True, configuration_parameter_boolean_true.boolean_value)

        configuration_parameter_boolean_no = baker.make(
            models.ConfigurationParameter,
            raw_value="No",
            parameter=parameter_boolean
        )

        self.assertEqual(False, configuration_parameter_boolean_no.boolean_value)

        configuration_parameter_boolean_yes = baker.make(
            models.ConfigurationParameter,
            raw_value="Yes",
            parameter=parameter_boolean
        )

        self.assertEqual(True, configuration_parameter_boolean_yes.boolean_value)
    
    def test_optional_string_param(self):
        """
        Should save raw_value in the string_value field
        if Parameter's value_type field is a optional and
        values field is string.
        """
        param_optional_string = baker.make(
            models.Parameter,
            value_type=models.Parameter.OPTIONAL,
            values=models.Parameter.STRING,
        )

        configuration_param_optional_string = baker.make(
            models.ConfigurationParameter,
            raw_value="test",
            parameter=param_optional_string,
        )

        self.assertEqual("test", configuration_param_optional_string.string_value)

    def test_optional_integer_param(self):
        """
        Should save raw_value in the integer_value field
        if Parameter's value_type field is a optional and
        values field is integer.
        """
        param_optional_integer = baker.make(
            models.Parameter,
            value_type=models.Parameter.OPTIONAL,
            values=models.Parameter.INTEGER,
        )

        configuration_param_optional_integer = baker.make(
            models.ConfigurationParameter,
            raw_value="123",
            parameter=param_optional_integer,
        )

        self.assertEqual(123, configuration_param_optional_integer.integer_value)

    def test_optional_boolean_param(self):
        """
        Should save raw_value in the boolean_value field
        if Parameter's value_type field is a optional and
        values field is boolean.
        """
        param_optional_boolean = baker.make(
            models.Parameter,
            value_type=models.Parameter.OPTIONAL,
            values=models.Parameter.BOOLEAN,
        )

        configuration_param_optional_boolean = baker.make(
            models.ConfigurationParameter,
            raw_value="True",
            parameter=param_optional_boolean,
        )

        self.assertEqual(True, configuration_param_optional_boolean.boolean_value)

    def test_optional_float_param(self):
        """
        Should save raw_value in the float_value field
        if Parameter's value_type field is a optional and
        values field is float.
        """
        param_optional_float = baker.make(
            models.Parameter,
            value_type=models.Parameter.OPTIONAL,
            values=models.Parameter.FLOAT,
        )

        configuration_param_optional_float = baker.make(
            models.ConfigurationParameter,
            raw_value="123.05",
            parameter=param_optional_float,
        )

        self.assertEqual(123.05, configuration_param_optional_float.float_value)

