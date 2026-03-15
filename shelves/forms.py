# shelves/forms.py
from django import forms
from .models import Shelf

class ShelfCreateForm(forms.ModelForm):
    class Meta:
        model = Shelf
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "maxlength": "80"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "maxlength": "280"}),
        }

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Please provide a shelf name.")
        return name

class ShelfUpdateForm(forms.ModelForm):
    class Meta:
        model = Shelf
        fields = {
            "name": "Shelf Name",
            "description": "Description",
            "is_public": "Make Public"
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "maxlength": "80"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "maxlength": "280"}),
            "is_public": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }