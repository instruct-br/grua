from django.contrib import admin
from core import models
from guardian.admin import GuardedModelAdmin


class MasterZoneAdmin(GuardedModelAdmin):
    pass


admin.site.register(models.MasterZone, MasterZoneAdmin)
admin.site.register(models.Node)
admin.site.register(models.Fact)
admin.site.register(models.PuppetClass)
admin.site.register(models.Parameter)
admin.site.register(models.Rule)
admin.site.register(models.FactRule)
admin.site.register(models.Group)
admin.site.register(models.Configuration)
admin.site.register(models.ConfigurationClass)
admin.site.register(models.ConfigurationParameter)
