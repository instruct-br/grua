import ast
import re
import uuid
from distutils.util import strtobool

from django.contrib.auth.models import User
from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from fernet_fields import EncryptedTextField
from taggit.managers import TaggableManager
from taggit.models import GenericUUIDTaggedItemBase, TaggedItemBase


class MasterZone(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    ca_cert = models.FileField(null=True)
    signed_cert = models.FileField(null=True)
    private_key = models.FileField(null=True)

    class Meta:
        permissions = (("has_access", "Has access to MasterZone"),)

    def __str__(self):
        return self.label

    def get_absolute_url(self):
        return reverse("master-zones-index")


class Environment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    master_zone = models.ForeignKey(
        MasterZone,
        on_delete=models.CASCADE,
        related_name="environments",
        related_query_name="environment",
    )

    def __str__(self):
        return self.name


class Node(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    certname = models.CharField(max_length=255)
    master_zone = models.ForeignKey(
        MasterZone,
        on_delete=models.CASCADE,
        related_name="nodes",
        related_query_name="node",
    )

    class Meta:
        unique_together = ("certname", "master_zone")

    def __str__(self):
        return self.certname


class Fact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    master_zone = models.ForeignKey(
        MasterZone,
        on_delete=models.CASCADE,
        related_name="facts",
        related_query_name="fact",
    )

    class Meta:
        unique_together = ("name", "master_zone")

    def __str__(self):
        return self.name


class PuppetClass(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    environment = models.ForeignKey(
        Environment,
        on_delete=models.CASCADE,
        related_name="classes",
        related_query_name="class",
    )

    def __str__(self):
        return self.name


class Parameter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    value_type = models.CharField(max_length=255, default="String")
    value_default = models.TextField(default="")
    values = models.CharField(max_length=255, blank=True)
    puppet_class = models.ForeignKey(
        PuppetClass,
        on_delete=models.CASCADE,
        related_name="parameters",
        related_query_name="parameter",
    )

    STRING = "String"
    INTEGER = "Integer"
    FLOAT = "Float"
    NUMERIC = "Numeric"
    BOOLEAN = "Boolean"
    ARRAY = "Array"
    HASH = "Hash"
    REGEXP = "Regexp"
    UNDEF = "Undef"
    DEFAULT = "Default"

    CORE_DATA_TYPES = (
        (STRING, STRING),
        (INTEGER, INTEGER),
        (FLOAT, FLOAT),
        (BOOLEAN, BOOLEAN),
        (ARRAY, ARRAY),
        (HASH, HASH),
        (REGEXP, REGEXP),
        (UNDEF, UNDEF),
        (DEFAULT, DEFAULT),
    )

    SCALAR = "Scalar"
    COLLECTION = "Collection"
    VARIANT = "Variant"
    DATA = "Data"
    PATTERN = "Pattern"
    ENUM = "Enum"
    TUPLE = "Tuple"
    STRUCT = "Struct"
    OPTIONAL = "Optional"
    CATALOGENTRY = "Catalogentry"
    TYPE = "Type"
    ANY = "Any"
    CALLABLE = "Callable"

    ABSTRACT_DATA_TYPES = (
        (SCALAR, SCALAR),
        (COLLECTION, COLLECTION),
        (VARIANT, VARIANT),
        (DATA, DATA),
        (PATTERN, PATTERN),
        (ENUM, ENUM),
        (TUPLE, TUPLE),
        (STRUCT, STRUCT),
        (OPTIONAL, OPTIONAL),
        (CATALOGENTRY, CATALOGENTRY),
        (TYPE, TYPE),
        (ANY, ANY),
        (CALLABLE, CALLABLE),
    )

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        re_pattern = r"([a-zA-Z]+)\[(.+)\]"
        match = re.search(re_pattern, self.value_type)
        if match is not None:
            self.value_type = match.group(1)
            self.values = match.group(2)

        if self.value_type == Parameter.BOOLEAN:
            self.values = "'True', 'False'"
        super().save(*args, **kwargs)


class UUIDTaggedItem(GenericUUIDTaggedItemBase, TaggedItemBase):
    """
    Necessary because we use non-integer primary keys
    """

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")


class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    description = models.TextField()
    matching_nodes = models.ManyToManyField(Node)
    tags = TaggableManager(through=UUIDTaggedItem, blank=True)
    environment = models.ForeignKey(
        Environment,
        on_delete=models.CASCADE,
        related_name="groups",
        related_query_name="group",
    )
    master_zone = models.ForeignKey(
        MasterZone,
        on_delete=models.CASCADE,
        related_name="groups",
        related_query_name="group",
    )

    def __str__(self):
        return self.label

    def get_absolute_url(self):
        return reverse("groups-index")

    @property
    def tags_list(self):
        return list(self.tags.all().values_list("name", flat=True))


class Rule(models.Model):
    ALL_RULES = "ALL"
    ANY_RULES = "ANY"

    MATCH_TYPE_CHOICES = ((ALL_RULES, "All rules"), (ANY_RULES, "Any rules"))

    group = models.OneToOneField(Group, on_delete=models.CASCADE, primary_key=True)
    nodes = models.ManyToManyField(Node)
    match_type = models.CharField(
        max_length=3, choices=MATCH_TYPE_CHOICES, default=ALL_RULES
    )

    def __str__(self):
        return self.group.label


class FactRule(models.Model):
    EQUALS = "="
    NOT_EQUAL = "!="
    MATCH = "~"
    NOT_MATCH = "!~"
    GREATER_THAN = ">"
    GREATER_OR_EQ_THAN = ">="
    LESS_THAN = "<"
    LESS_OR_EQ_THAN = "<="

    OPERATOR_CHOICES = (
        (EQUALS, EQUALS),
        (NOT_EQUAL, NOT_EQUAL),
        (MATCH, MATCH),
        (NOT_MATCH, NOT_MATCH),
        (GREATER_THAN, GREATER_THAN),
        (GREATER_OR_EQ_THAN, GREATER_OR_EQ_THAN),
        (LESS_THAN, LESS_THAN),
        (LESS_OR_EQ_THAN, LESS_OR_EQ_THAN),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fact = models.ForeignKey(
        Fact, on_delete=models.CASCADE, related_name="rules", related_query_name="rule"
    )
    rule = models.ForeignKey(
        Rule, on_delete=models.CASCADE, related_name="facts", related_query_name="fact"
    )
    operator = models.CharField(max_length=3, choices=OPERATOR_CHOICES, default=EQUALS)
    value = models.CharField(max_length=255)

    def __str__(self):
        return self.fact.name


class Configuration(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return self.group.label


class ConfigurationClass(models.Model):
    configuration = models.ForeignKey(
        Configuration,
        on_delete=models.CASCADE,
        related_name="classes",
        related_query_name="class",
    )
    puppet_class = models.ForeignKey(
        PuppetClass,
        on_delete=models.CASCADE,
        related_name="groups",
        related_query_name="group",
    )

    def __str__(self):
        return self.puppet_class.name


class ConfigurationParameter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    raw_value = models.TextField(blank=True)
    string_value = models.TextField(null=True, blank=True)
    integer_value = models.IntegerField(null=True, blank=True)
    float_value = models.FloatField(null=True, blank=True)
    boolean_value = models.NullBooleanField(null=True, blank=True)
    sensitive_value = EncryptedTextField(null=True, blank=True)
    configuration_class = models.ForeignKey(
        ConfigurationClass,
        on_delete=models.CASCADE,
        related_name="parameters",
        related_query_name="parameter",
    )
    parameter = models.ForeignKey(
        Parameter,
        on_delete=models.CASCADE,
        related_name="classifications",
        related_query_name="classification",
    )

    def __str__(self):
        return self.parameter.name

    def cast(self, value_type, value):
        if value_type == Parameter.STRING:
            converted = str(value)
        elif value_type == Parameter.INTEGER:
            converted = int(value)
        elif value_type == Parameter.FLOAT:
            converted = float(value)
        elif value_type == Parameter.BOOLEAN:
            converted = bool(strtobool(value))
        elif value_type == Parameter.HASH:
            converted = ast.literal_eval(value)
        elif value_type == Parameter.ARRAY:
            converted = ast.literal_eval(value)
        else:
            converted = value

        return converted

    def save(self, *args, **kwargs):
        if self.parameter.value_type == Parameter.OPTIONAL:
            value_type = self.parameter.values
        else:
            value_type = self.parameter.value_type

        if re.search("^sensitive_.*", self.parameter.name):
            self.sensitive_value = self.raw_value
            self.raw_value = "[Sensitive]"
        elif value_type == Parameter.STRING:
            self.string_value = self.cast(value_type, self.raw_value)
        elif value_type == Parameter.INTEGER:
            self.integer_value = self.cast(value_type, self.raw_value)
        elif value_type == Parameter.FLOAT:
            self.float_value = self.cast(value_type, self.raw_value)
        elif value_type == Parameter.BOOLEAN:
            self.boolean_value = self.cast(value_type, self.raw_value)

        super().save(*args, **kwargs)

    def get_value(self):
        optional_values = {
            Parameter.BOOLEAN: self.boolean_value,
            Parameter.FLOAT: self.float_value,
            Parameter.INTEGER: self.integer_value,
            Parameter.STRING: self.string_value,
        }

        obj_dict = model_to_dict(self)
        value = obj_dict.get(self.parameter.value_type.lower() + "_value", None)

        if value is None:
            if re.search("^sensitive_.*", self.parameter.name):
                if self.parameter.values == "":
                    param_type = self.parameter.value_type
                else:
                    param_type = self.parameter.values

                value = self.cast(param_type, obj_dict.get("sensitive_value", None))

            elif self.parameter.value_type == Parameter.HASH:
                value = self.cast(self.parameter.value_type, self.raw_value)
            elif self.parameter.value_type == Parameter.ARRAY:
                value = self.cast(self.parameter.value_type, self.raw_value)
            elif self.parameter.value_type == Parameter.OPTIONAL:
                value = optional_values.get(self.parameter.values, self.raw_value)
            else:
                value = self.raw_value

        return value

    def get_raw_value(self):
        if re.search("^sensitive_.*", self.parameter.name):
            raw_value = self.sensitive_value
        else:
            raw_value = self.raw_value

        return raw_value


class Variable(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, primary_key=True)
    data = HStoreField(null=True)

    def __str__(self):
        return self.group.label


class UserLog(models.Model):
    """
    Model for user action logging
    """

    # user is nullable in case of AnonymousUser
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="logs",
        related_query_name="log",
    )
    request_path = models.CharField(max_length=256)
    request_method = models.CharField(max_length=10)
    response_code = models.CharField(max_length=3)
    datetime = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    @property
    def formatted_user(self):
        if not self.user:
            return "-----"
        return self.user

    @staticmethod
    def list_headers():
        return ["User", "Datetime", "Path", "Method", "Response Code", "IP"]

    def list_data(self):
        return [
            self.formatted_user,
            self.datetime,
            self.request_path,
            self.request_method,
            self.response_code,
            self.ip_address,
        ]


@receiver(post_save, sender=Group)
def group_create_handler(sender, **kwargs):
    """
    Signal receiver for Group creation
    Should create the associated Rule, Configuration and Variable
    """
    if kwargs["created"]:
        Configuration.objects.create(group=kwargs["instance"])
        Rule.objects.create(group=kwargs["instance"])
        Variable.objects.create(group=kwargs["instance"])
