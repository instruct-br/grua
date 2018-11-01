from django import forms
from core import models
from taggit.forms import TagWidget


class CustomTagWidget(TagWidget):
    input_type = "hidden"


class GroupForm(forms.ModelForm):

    class Meta:
        model = models.Group
        fields = ("master_zone", "environment", "label", "description", "tags")
        widgets = {"tags": CustomTagWidget(attrs={"placeholder": "Group tags"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["environment"].queryset = models.Environment.objects.none()

        if "master_zone" in self.data:
            try:
                master_zone = models.MasterZone.objects.get(
                    id=self.data.get("master_zone")
                )
                self.fields["environment"].queryset = master_zone.environments.all()
            except (ValueError, TypeError):
                pass
