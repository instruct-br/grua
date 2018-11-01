from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from core import models
from frontend import forms
from taggit.models import Tag
from guardian.shortcuts import get_objects_for_user, assign_perm


class MasterZonePermissionRequiredMixin(PermissionRequiredMixin):
    permission_required = "core.has_access"
    raise_exception = True

    def has_permission(self):
        """
        Checks user permission to Zone object
        Treats Zones, Masters and Groups
        """
        perms = self.get_permission_required()
        obj = self.get_object()
        if isinstance(obj, models.MasterZone):
            obj = obj
        elif isinstance(obj, models.Group):
            obj = obj.master_zone
        return self.request.user.has_perms(perms, obj)


def _order_by_value(value, request):
    order_by = request.GET.get("order_by")
    return "-" + value if order_by and order_by == value else value


class MasterZoneListView(LoginRequiredMixin, ListView):
    model = models.MasterZone
    paginate_by = 10
    ordering = ("label",)
    template_name = "master_zones/index.html"

    def get_queryset(self):
        """
        Filter by user permission to MasterZone
        """

        queryset = get_objects_for_user(self.request.user, "core.has_access")

        if self.request.GET.get("clear", None):
            self.request.session["master_zone_list_filter"] = {}
            return queryset.distinct().order_by("label")

        if self.request.method == "POST":
            master_zone_list_filter = {"label": self.request.POST.get("label", "")}
            self.request.session["master_zone_list_filter"] = master_zone_list_filter
        else:
            master_zone_list_filter = self.request.session.get(
                "master_zone_list_filter", {}
            )

        label = master_zone_list_filter.get("label")
        if label:
            queryset = queryset.filter(label__icontains=label)

        order_by = self.request.GET.get("order_by", "label")

        if "master_zone" in self.request.GET:
            queryset = queryset.filter(id=self.request.GET["master_zone"])

        return queryset.order_by(order_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["master_zone_list_filter"] = self.request.session.get(
            "master_zone_list_filter", {}
        )

        context["order_by"] = {
            "label": _order_by_value("label", self.request),
            "address": _order_by_value("address", self.request),
        }
        return context

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class MasterZoneCreate(LoginRequiredMixin, CreateView):
    model = models.MasterZone
    fields = ("label", "address")
    template_name = "master_zones/create.html"

    def form_valid(self, form):
        """
        Assign permission to Zone creator
        """
        self.object = form.save()
        assign_perm("core.has_access", self.request.user, self.object)
        return super().form_valid(form)


class MasterZoneEdit(LoginRequiredMixin, MasterZonePermissionRequiredMixin, UpdateView):
    model = models.MasterZone
    fields = ("label", "address")
    template_name = "master_zones/edit.html"

    def get_form(self, **kwargs):
        """
        Filter MasterZones field queryset
        """
        form = super().get_form(**kwargs)
        form.queryset = get_objects_for_user(self.request.user, "core.has_access")
        return form


class MasterZoneDelete(
    LoginRequiredMixin, MasterZonePermissionRequiredMixin, DeleteView
):
    model = models.MasterZone
    template_name = "master_zones/index.html"
    success_url = reverse_lazy("master-zones-index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["deleting"] = True
        context["cancel_delete"] = "master-zones-index"
        return context


class GroupListView(LoginRequiredMixin, ListView):
    model = models.Group
    paginate_by = 10
    ordering = ("label",)
    template_name = "groups/index.html"

    def get_queryset(self):
        """
        Filter by Master, tags and user permission to Group
        """
        qs_filter = {
            "master_zone__in": get_objects_for_user(
                self.request.user, "core.has_access"
            )
        }

        if "clear" in self.request.GET:
            self.master_zone = None
            self.environment = None
            self.request.session["group_list_filter"] = {}
            return models.Group.objects.filter(**qs_filter).distinct().order_by("label")

        if self.request.method == "POST":
            group_list_filter = {
                "tags": self.request.POST.get("tags", ""),
                "label": self.request.POST.get("label", ""),
                "environment__name": self.request.POST.get("environment__name", ""),
                "description": self.request.POST.get("description", ""),
                "master_zone": self.request.POST.get("master_zone", ""),
            }
            self.request.session["group_list_filter"] = group_list_filter
        else:
            group_list_filter = self.request.session.get("group_list_filter", {})
            if "master_zone" in self.request.GET:
                group_list_filter["master_zone"] = self.request.GET.get("master_zone")
                self.request.session["group_list_filter"] = group_list_filter

        tags = group_list_filter.get("tags")

        if tags:
            tags = tags.replace('"', "")
            qs_filter["tags__name__in"] = tags.split(",")

        if group_list_filter.get("master_zone"):
            self.master_zone = get_object_or_404(
                models.MasterZone, pk=group_list_filter.get("master_zone")
            )
            qs_filter["master_zone"] = self.master_zone
        else:
            self.master_zone = None

        label = group_list_filter.get("label")
        if label:
            qs_filter["label__icontains"] = label

        environment_name = group_list_filter.get("environment__name")
        if environment_name:
            qs_filter["environment__name"] = environment_name

        description = group_list_filter.get("description")
        if description:
            qs_filter["description__icontains"] = description

        order_by = self.request.GET.get("order_by", "label")

        return models.Group.objects.filter(**qs_filter).distinct().order_by(order_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["master_zone"] = self.master_zone
        context["all_tags"] = list(Tag.objects.all().values_list("name", flat=True))
        context["group_list_filter"] = self.request.session.get("group_list_filter", {})

        context["order_by"] = {
            "label": _order_by_value("label", self.request),
            "master_zone__label": _order_by_value("master_zone__label", self.request),
            "environment__name": _order_by_value("environment__name", self.request),
            "description": _order_by_value("description", self.request),
        }

        context["all_master_zones"] = []
        for master_zone in models.MasterZone.objects.all().values("id", "label"):
            master_zone["id"] = str(master_zone["id"])
            context["all_master_zones"].append(master_zone)

        context["all_environments_names"] = list(
            models.Environment.objects.all().values_list("name", flat=True).distinct()
        )

        return context

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


def group_detail_classes(request, pk):
    group = models.Group.objects.get(id=pk)
    return render(
        request,
        "groups/classes.html",
        {"group": group, "master_zone": group.master_zone},
    )


def group_detail_nodes(request, pk):
    group = models.Group.objects.get(id=pk)
    return render(
        request,
        "groups/nodes.html",
        {"group": group, "nodes": group.matching_nodes.all()},
    )


def group_detail_rules(request, pk):
    group = models.Group.objects.get(id=pk)
    master_zone = group.master_zone
    return render(
        request, "groups/rules.html", {"group": group, "master_zone": master_zone}
    )


def group_detail_variables(request, pk):
    group = models.Group.objects.get(id=pk)
    master_zone = group.master_zone
    return render(
        request, "groups/variables.html", {"group": group, "master_zone": master_zone}
    )


def group_environments_options(request):
    master_zone = models.MasterZone.objects.get(id=request.GET.get("master_zone"))
    environments = master_zone.environments.all()
    return render(request, "groups/environments.html", {"environments": environments})


class GroupCreate(LoginRequiredMixin, CreateView):
    model = models.Group
    form_class = forms.GroupForm
    template_name = "groups/create.html"

    def get_form(self, **kwargs):
        """
        Filter Masters field queryset
        """
        form = super().get_form(**kwargs)
        form.fields["master_zone"].queryset = get_objects_for_user(
            self.request.user, "core.has_access"
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["all_tags"] = list(Tag.objects.all().values_list("name", flat=True))
        return context


class GroupEdit(LoginRequiredMixin, MasterZonePermissionRequiredMixin, UpdateView):
    model = models.Group
    form_class = forms.GroupForm
    template_name = "groups/edit.html"

    def get_form(self, **kwargs):
        """
        Filter Masters field queryset
        """
        form = super().get_form(**kwargs)
        form.fields["master_zone"].queryset = get_objects_for_user(
            self.request.user, "core.has_access"
        )
        form.fields.pop("environment")
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["all_tags"] = list(Tag.objects.all().values_list("name", flat=True))
        return context


class GroupDelete(LoginRequiredMixin, MasterZonePermissionRequiredMixin, DeleteView):
    model = models.Group
    template_name = "groups/index.html"
    success_url = reverse_lazy("groups-index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["deleting"] = True
        context["cancel_delete"] = "groups-index"
        return context


class UserLogListView(PermissionRequiredMixin, ListView):
    model = models.UserLog
    paginate_by = 50
    ordering = ("-datetime",)
    template_name = "logs.html"

    def has_permission(self):
        """
        Checks if user is superuser
        """
        return self.request.user.is_superuser

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_headers"] = models.UserLog.list_headers()
        return context


def docs_view(request):
    """
    Show all API reference documentation
    """
    return render(request, "documentation/index.html")
