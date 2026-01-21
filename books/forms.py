from django import forms


class OpenLibrarySearchForm(forms.Form):
    q = forms.CharField(
        required=True,
        max_length=200,
        label='Search',
        widget=forms.TextInput(attrs={
            "placeholder": "Title, author, subject…",
            "class": "form-control me-2 w-100",
            }),        
    )
    
    page = forms.IntegerField(required=False, min_value=1)
    
    def clean_q(self):
        return " ".join(self.cleaned_data['q'].split())