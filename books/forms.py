from django import forms
from django.core.validators import RegexValidator


class OmniSearchForm(forms.Form):
    q = forms.CharField(
        required=True,
        max_length=200,
        label='Search',
        widget=forms.TextInput(attrs={
            "placeholder": "Title, author, subject…",
            "class": "form-control me-2",
            }),        
    )
    
    page = forms.IntegerField(required=False, min_value=1)
    
    def clean_q(self):
        return " ".join(self.cleaned_data['q'].split())
    
    
    
numeric_only = RegexValidator(
    regex=r'^\d*$',
    message='Only numeric characters are allowed.'
)

class AdvancedSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        max_length=200,
        label='query',
        widget=forms.TextInput(attrs={
            "placeholder": "Title, author, subject…",
            "class": "form-control my-2",
            }),        
    )
    
    title = forms.CharField(
        required=False,
        max_length=200,
        label='Book Title',
        widget=forms.TextInput(attrs={
            'placeholder': 'Book Title',
            'class': 'form-control my-2'
        })
    )
    
    author = forms.CharField(
        required=False,
        max_length=200,
        label='Author',
        widget=forms.TextInput(attrs={
            'placeholder': 'Author',
            'class': 'form-control my-2'
        })
    )
    
    language = forms.ChoiceField(
        choices={
            "en": "English",
            "es": "Español",
            "pt": "Português",
            "fr": "Français",
            "de": "Deutsch",
            "it": "Italiano",
            "nl": "Nederlands",
            "sv": "Svenska",
            "no": "Norsk",
            "da": "Dansk",
            "fi": "Suomi",
            "pl": "Polski",
            "cs": "Čeština",
            "hu": "Magyar",
            "ro": "Română",
            },
        required=False,
        label='Language',
        widget=forms.Select(attrs={
            'class': 'form-control form-select my-2'
        })
    )
    
    page = forms.IntegerField(required=False, min_value=1)
    