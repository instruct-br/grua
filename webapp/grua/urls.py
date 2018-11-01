"""GRUA URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf.urls import url
from django.conf.urls.static import static
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as drf_views
from api import views as api_views
from frontend import views as frontend_views
from grua import settings
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


router = DefaultRouter()
router.register(r"environments", api_views.EnvironmentViewSet)
router.register(r"master_zones", api_views.MasterZoneViewSet)
router.register(r"environments", api_views.EnvironmentViewSet)
router.register(r"facts", api_views.FactViewSet)
router.register(r"nodes", api_views.NodeViewSet)
router.register(r"classes", api_views.PuppetClassViewSet)
router.register(r"parameters", api_views.ParameterViewSet)
router.register(r"configuration", api_views.ConfigurationViewSet)
router.register(r"rules", api_views.RuleViewSet)
router.register(r"variables", api_views.VariableViewSet)
router.register(r"groups", api_views.GroupViewSet)


schema_view = get_schema_view(
    openapi.Info(
        title="API Documentation",
        default_version="v1",
        description="",
        terms_of_service="https://www.google.com/policies/terms/",
    ),
    public=True,
    permission_classes=(permissions.IsAdminUser,),
)

urlpatterns = [
    path("", frontend_views.MasterZoneListView.as_view(), name="index"),
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls")),
    path("api-token-auth/", drf_views.obtain_auth_token),
    path("api/", include(router.urls)),
    path(
        "master_zones/",
        frontend_views.MasterZoneListView.as_view(),
        name="master-zones-index",
    ),
    path(
        "master_zones/new/",
        frontend_views.MasterZoneCreate.as_view(),
        name="master-zones-new",
    ),
    path(
        "master_zones/edit/<uuid:pk>",
        frontend_views.MasterZoneEdit.as_view(),
        name="master-zones-edit",
    ),
    path(
        "master_zones/delete/<uuid:pk>",
        frontend_views.MasterZoneDelete.as_view(),
        name="master-zones-delete",
    ),
    path("groups/", frontend_views.GroupListView.as_view(), name="groups-index"),
    path("groups/new/", frontend_views.GroupCreate.as_view(), name="groups-new"),
    path(
        "groups/classes/<uuid:pk>",
        frontend_views.group_detail_classes,
        name="groups-classes",
    ),
    path(
        "groups/nodes/<uuid:pk>", frontend_views.group_detail_nodes, name="groups-nodes"
    ),
    path(
        "groups/rules/<uuid:pk>", frontend_views.group_detail_rules, name="groups-rules"
    ),
    path(
        "groups/variables/<uuid:pk>",
        frontend_views.group_detail_variables,
        name="groups-variables",
    ),
    path(
        "groups/new/environments-options/",
        frontend_views.group_environments_options,
        name="environments-options",
    ),
    path(
        "groups/edit/<uuid:pk>", frontend_views.GroupEdit.as_view(), name="groups-edit"
    ),
    path(
        "groups/delete/<uuid:pk>",
        frontend_views.GroupDelete.as_view(),
        name="groups-delete",
    ),
    path("logs/", frontend_views.UserLogListView.as_view(), name="logs-index"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("docs/", frontend_views.docs_view, name="api-documentation"),
    re_path(
        "docs/swagger(?P<format>\.json|\.yaml)",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    path(
        "docs/swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "docs/redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
