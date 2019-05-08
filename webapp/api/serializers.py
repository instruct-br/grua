import ast
from functools import reduce
from django.db.models import F
from rest_framework import serializers
from core.models import (
    MasterZone,
    Environment,
    Fact,
    Node,
    PuppetClass,
    Parameter,
    Group,
    FactRule,
    Rule,
    Variable,
    Configuration,
    ConfigurationClass,
    ConfigurationParameter,
)


class MasterZoneSerializer(serializers.ModelSerializer):

    class Meta:
        model = MasterZone
        fields = ("id", "label", "address", "ca_cert", "signed_cert", "private_key")

    def to_representation(self, instance):
        data = super(MasterZoneSerializer, self).to_representation(instance)
        data["environments_names"] = list(
            instance.environments.all().values_list("name", flat=True)
        )
        return data


class EnvironmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Environment
        fields = ("id", "name", "master_zone")
        extra_kwargs = {"id": {"read_only": True, "required": False}}


class FactSerializer(serializers.ModelSerializer):

    class Meta(object):
        model = Fact
        fields = ("id", "name", "master_zone")


class NodeSerializer(serializers.ModelSerializer):

    class Meta(object):
        model = Node
        fields = ("id", "certname", "master_zone")


class PuppetClassSerializer(serializers.ModelSerializer):

    class Meta(object):
        model = PuppetClass
        fields = ("id", "name", "environment")


class ParameterSerializer(serializers.ModelSerializer):
    type = serializers.CharField(read_only=True, source="value_type")
    default = serializers.CharField(read_only=True, source="value_default")
    values = serializers.SerializerMethodField()

    class Meta(object):
        model = Parameter
        fields = ("id", "name", "puppet_class", "type", "default", "values")

    def get_values(self, obj):
        if obj.value_type in [Parameter.ENUM, Parameter.BOOLEAN]:
            values = ast.literal_eval(obj.values)
        else:
            values = obj.values
        return values


class ConfigurationParameterSlugSerializer(serializers.SlugRelatedField):

    def get_queryset(self):
        """
        Return parameters from puppet class from the same master of the group
        """
        puppet_class = self.root.context["puppet_class"]
        group = self.root.instance.group
        query = {"environment": group.environment, "name": puppet_class}
        return Parameter.objects.filter(
            puppet_class__in=PuppetClass.objects.filter(**query)
        )


class ConfigurationParameterSerializer(serializers.ModelSerializer):
    parameter = ConfigurationParameterSlugSerializer(slug_field="name")
    value = serializers.SerializerMethodField()

    class Meta(object):
        model = ConfigurationParameter
        fields = ("value", "raw_value", "parameter")

    def get_value(self, obj):
        return obj.get_value()


class ConfigurationClassSlugSerializer(serializers.SlugRelatedField):

    def get_queryset(self):
        """
        Returns puppet classes from the same master of the group
        """
        group = self.root.instance.group
        return PuppetClass.objects.filter(environment=group.environment)


class ConfigurationClassSerializer(serializers.ModelSerializer):
    parameters = ConfigurationParameterSerializer(many=True)
    puppet_class = ConfigurationClassSlugSerializer(slug_field="name")

    class Meta(object):
        model = ConfigurationClass
        fields = ("puppet_class", "parameters")

    def to_internal_value(self, data):
        self.root.context["puppet_class"] = data["puppet_class"]
        return super().to_internal_value(data)


class ConfigurationSerializer(serializers.ModelSerializer):
    classes = ConfigurationClassSerializer(many=True)

    class Meta(object):
        model = Configuration
        fields = ("classes",)

    def update(self, instance, validated_data):
        classes = validated_data.pop("classes")

        # Create each ConfigurationClass
        for config_class in classes:
            params = config_class.pop("parameters")
            config_class_obj, _ = ConfigurationClass.objects.update_or_create(
                configuration=instance, puppet_class=config_class["puppet_class"]
            )
            # Create each ConfigurationParameter
            for param in params:
                ConfigurationParameter.objects.update_or_create(
                    configuration_class=config_class_obj,
                    parameter=param["parameter"],
                    defaults={"raw_value": param["raw_value"]},
                )
            # Remove ConfigurationParameter that are not used anymore
            ConfigurationParameter.objects.filter(
                configuration_class=config_class_obj
            ).exclude(
                parameter__name__in=(param["parameter"] for param in params)
            ).delete()

        # Remove ConfigurationClass that are not used anymore
        ConfigurationClass.objects.filter(configuration=instance).exclude(
            puppet_class__in=(pp_class["puppet_class"] for pp_class in classes)
        ).delete()

        return instance


class RuleFactSlugSerializer(serializers.SlugRelatedField):

    def get_queryset(self):
        """
        Returns facts from the same master_zone of the group
        """
        return Fact.objects.filter(master_zone=self.root.instance.group.master_zone)


class RuleFactSerializer(serializers.ModelSerializer):
    fact = RuleFactSlugSerializer(slug_field="name")

    class Meta(object):
        model = FactRule
        fields = ("fact", "operator", "value")


class RuleNodeSerializer(serializers.SlugRelatedField):

    def get_queryset(self):
        """
        Returns nodes from the same master_zone of the group
        """
        return Node.objects.filter(master_zone=self.root.instance.group.master_zone)


class RuleSerializer(serializers.ModelSerializer):
    facts = RuleFactSerializer(many=True)
    nodes = RuleNodeSerializer(many=True, slug_field="certname")

    class Meta(object):
        model = Rule
        fields = ("match_type", "nodes", "facts")

    def update(self, instance, validated_data):
        facts = validated_data.get("facts", [])
        fact_names = []
        for fact in facts:
            fact_name = fact.pop("fact")
            FactRule.objects.update_or_create(
                fact=fact_name, rule=instance, defaults=fact
            )
            fact_names.append(fact_name)

        if not self.partial:
            FactRule.objects.filter(rule=instance).exclude(
                fact__in=(fact_name for fact_name in fact_names)
            ).delete()
            instance.nodes.set(validated_data.pop("nodes"))
        else:
            for fact in facts:
                fact_name = fact.get("fact", "")
                if fact_name:
                    FactRule.objects.update_or_create(
                        fact=fact_name, rule=instance, defaults=fact
                    )

            for node in validated_data.get("nodes", []):
                instance.nodes.add(node)

        instance.match_type = validated_data.get("match_type", instance.match_type)

        instance.save()
        return instance


class VariableSerializer(serializers.ModelSerializer):

    class Meta(object):
        model = Variable
        fields = ("data",)


class GroupNodeSerializer(serializers.SlugRelatedField):

    def get_queryset(self):
        """
        Returns nodes from the same master_zone of the group
        """
        queryset = Node.objects.all()
        if self.root.instance:
            queryset = queryset.filter(master_zone=self.root.instance.master_zone)
        return queryset


class GroupSerializer(serializers.ModelSerializer):
    matching_nodes = GroupNodeSerializer(
        required=False, many=True, slug_field="certname"
    )
    id = serializers.CharField(read_only=True)
    tags_list = serializers.ListField(required=False)

    class Meta(object):
        model = Group
        fields = (
            "id",
            "label",
            "matching_nodes",
            "master_zone",
            "environment",
            "description",
            "tags_list",
        )
        extra_kwargs = {
            "matching_nodes": {"write_only": True},
            "environment": {"required": False},
        }

    def create(self, validated_data):
        tags_list = validated_data.pop("tags_list", "")
        nodes_list = validated_data.pop("matching_nodes", "")
        if "environment" not in validated_data:
            validated_data["environment"] = Environment.objects.get(
                name="production", master_zone_id=validated_data["master_zone"]
            )
        new_group = Group.objects.create(**validated_data)
        if tags_list:
            new_group.tags.set(*tags_list)
        if nodes_list:
            new_group.matching_nodes.set(*nodes_list)
        return new_group


class NodeClassifierSerializer(serializers.ModelSerializer):
    classes = serializers.SerializerMethodField()
    parameters = serializers.SerializerMethodField()
    environment = serializers.SerializerMethodField()

    class Meta(object):
        model = Node
        fields = ("classes", "parameters", "environment")

    def get_classes(self, node):
        """
        Returns puppet classes, parameters and values
        Example:
        {
            'class_name1': [
                {'param_name1': 'param_value1'},
                {'param_name2': 'param_value2'}
            ],
            'class_name2': []
        }
        """
        classes = {}
        values = (
            node.group_set.filter(
                configuration__class__puppet_class__name__isnull=False
            )
            .annotate(
                class_name=F("configuration__class__puppet_class__name"),
                param_name=F("configuration__class__puppet_class__parameter__name"),
                param_value=F(
                    "configuration__class__puppet_class__parameter__classification__raw_value"
                ),  # noqa
            )
            .values("class_name", "param_name", "param_value")
        )

        for value in values:
            if value["class_name"] not in classes:
                classes[value["class_name"]] = None
            if value["param_name"]:
                if value["param_value"] is not None:
                    if classes[value["class_name"]] is None:
                        classes[value["class_name"]] = {}
                    param_value = (
                        ConfigurationParameter.objects.filter(
                            parameter__name=value["param_name"]
                        )
                        .first()
                        .get_value()
                    )
                    classes[value["class_name"]][value["param_name"]] = param_value

        # Returns None for nodes withou classification settings
        return classes or None

    def get_parameters(self, node):
        """
        Returns list of hash values from Variable related to the node's group
        """
        variables = node.group_set.filter(variable__data__isnull=False).values_list(
            "variable__data", flat=True
        )
        # Returns None for nodes withou classification settings
        return reduce(lambda x, y: {**x, **y}, variables, {}) or None

    def get_environment(self, node):
        groups = node.group_set.all()
        return str(groups.first().environment) if groups else None
