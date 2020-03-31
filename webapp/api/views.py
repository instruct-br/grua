import faktory
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_yaml.renderers import YAMLRenderer
from rest_framework_yaml.encoders import SafeDumper
from core.models import (
    MasterZone,
    Environment,
    Fact,
    Node,
    PuppetClass,
    Parameter,
    Group,
    Configuration,
    Rule,
    Variable,
)
from api.serializers import (
    EnvironmentSerializer,
    MasterZoneSerializer,
    FactSerializer,
    NodeSerializer,
    PuppetClassSerializer,
    ParameterSerializer,
    ConfigurationSerializer,
    RuleSerializer,
    VariableSerializer,
    GroupSerializer,
    NodeClassifierSerializer,
)


def represent_none(self, _):
    return self.represent_scalar("tag:yaml.org,2002:null", "")


SafeDumper.add_representer(type(None), represent_none)


class EnvironmentViewSet(viewsets.ModelViewSet):
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer
    pagination_class = None


class MasterZoneViewSet(viewsets.ModelViewSet):
    queryset = MasterZone.objects.all()
    serializer_class = MasterZoneSerializer
    pagination_class = None

    @action(methods=["post"], detail=False)
    def refresh_info(self, request):
        master_id = request.data.get("master_id", None)
        try:
            master_zone = MasterZone.objects.get(id=master_id)
            master_address = master_zone.address
        except MasterZone.DoesNotExist:
            return Response({"failure": "Master Zone does not exist"})

        with faktory.connection() as client:
            states = {
                "environments_updated": client.queue(
                    "master-environments", args=(master_id,), priority=6
                ),
                "facts_updated": client.queue(
                    "master-facts", args=(master_id, master_address), priority=6
                ),
                "nodes_updated": client.queue(
                    "master-nodes", args=(master_id, master_address), priority=6
                ),
                "classes_updated": client.queue(
                    "master-classes",
                    args=(
                        master_id,
                        list(
                            master_zone.environments.all().values_list(
                                "name", flat=True
                            )
                        ),
                    ),
                    priority=6,
                ),
            }
        return Response({"success": states})

    @action(methods=["post"], detail=False)
    def environments_sync(self, request):
        data = request.data
        try:
            master_zone = MasterZone.objects.get(id=data["master_id"])
        except MasterZone.DoesNotExist:
            return Response({"failure": "Master Zone does not exist"})

        for name in data["environments"]:
            env, _ = Environment.objects.get_or_create(
                name=name, master_zone=master_zone
            )

        return Response({"status": "ok"})


class FactViewSet(viewsets.ModelViewSet):
    queryset = Fact.objects.all()
    serializer_class = FactSerializer
    pagination_class = None
    filter_fields = ("master_zone",)

    @action(methods=["post"], detail=False)
    def sync(self, request):
        data = [
            fact for fact in request.data if not Fact.objects.filter(**fact).exists()
        ]
        serializer = self.get_serializer(data=data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "ok"})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NodeViewSet(viewsets.ModelViewSet):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer
    pagination_class = None
    filter_fields = ("master_zone",)

    @action(methods=["post"], detail=False)
    def sync(self, request):
        data = [
            node for node in request.data if not Node.objects.filter(**node).exists()
        ]
        serializer = self.get_serializer(data=data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": "ok"})
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=["get"],
        detail=False,
        renderer_classes=(YAMLRenderer,),
        serializer_class=NodeClassifierSerializer,
    )
    def node_classifier(self, request):
        certname = request.query_params.get("certname", "")
        master_id = request.query_params.get("master_id", "")
        error_message = ""
        try:
            node = Node.objects.get(certname=certname, master_zone__id=master_id)
        except Node.DoesNotExist:
            # Instantiate a dummy node to produce an empty answer
            node = Node()
        except MasterZone.DoesNotExist:
            error_message = 'Master with id "%s" not found' % master_id
        except ValidationError:
            error_message = "Invalid certname or master_id parameters"
        if error_message:
            return JsonResponse(
                {"error": error_message}, status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(node)
        response = Response(serializer.data, content_type="text/yaml")
        cd = 'attachment; filename="%s_classifier.yml"' % node.certname
        response["Content-Disposition"] = cd
        return response


class PuppetClassViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PuppetClass.objects.all()
    serializer_class = PuppetClassSerializer
    pagination_class = None
    filter_fields = ("environment",)

    @action(methods=["post"], detail=False)
    def sync(self, request):
        for class_def in request.data:
            environment, _ = Environment.objects.get_or_create(
                name=class_def["environment"], master_zone_id=class_def["master"]
            )
            ppclass, _ = PuppetClass.objects.get_or_create(
                name=class_def["name"], environment=environment
            )
            param_names = [param["name"] for param in class_def["params"]]
            for param in class_def["params"]:
                Parameter.objects.get_or_create(
                    name=param["name"],
                    puppet_class=ppclass,
                    defaults={
                        "value_type": param["type"],
                        "value_default": param.get("default_source", ""),
                    },
                )
            Parameter.objects.filter(puppet_class=ppclass).exclude(
                name__in=param_names
            ).delete()
        if any(request.data):
            env_names = (class_def["environment"] for class_def in request.data)
            master_zone = request.data[0]["master"]
            for env_name in env_names:
                class_names = (
                    class_def["name"]
                    for class_def in request.data
                    if class_def["environment"] == env_name
                )
                environment = Environment.objects.get(
                    name=env_name, master_zone_id=master_zone
                )
                PuppetClass.objects.filter(environment=environment).exclude(
                    name__in=class_names
                ).delete()
        return Response({"status": "ok"})


class ParameterViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Additional endpoint

    ***
        /types
        Parameter possible types, followed by a boolean value
        that indicates if the type needs a 'values' field or not
    ***
    """
    queryset = Parameter.objects.all()
    serializer_class = ParameterSerializer
    pagination_class = None
    filter_fields = ("puppet_class",)

    @action(methods=["get"], url_path="types", detail=False)
    def types(self, request):
        types = dict((t, False) for _, t in Parameter.CORE_DATA_TYPES)
        types.update(dict((t, True) for _, t in Parameter.ABSTRACT_DATA_TYPES))
        return Response(types)


class ConfigurationViewSet(viewsets.ModelViewSet):
    queryset = Configuration.objects.all()
    serializer_class = ConfigurationSerializer
    pagination_class = None


class RuleViewSet(viewsets.ModelViewSet):
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer
    pagination_class = None

    def process_response(self, response, pk):
        if response.status_code == 200:
            rule = self.get_object()
            master_id = str(rule.group.master_zone.id)
            master_address = rule.group.master_zone.address
            with faktory.connection() as client:
                client.queue("group-nodes", args=(pk, master_id, master_address))

    def update(self, request, pk=None):
        response = super().update(request, pk)
        self.process_response(response, pk)
        return response

    def partial_update(self, request, pk=None):
        response = super().update(request, pk, partial=True)
        self.process_response(response, pk)
        return response


class VariableViewSet(viewsets.ModelViewSet):
    queryset = Variable.objects.all()
    serializer_class = VariableSerializer
    pagination_class = None


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    pagination_class = None
