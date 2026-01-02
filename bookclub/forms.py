from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django import forms
from turnstile.fields import TurnstileField

from .models import Profile
from users.models import CustomUser


class RegisterNewUser(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = [
            'username',
            'email',
            'password1',
            'password2'
        ]
        labels = {
            "username": "Username:",
            "email": "Email Address:",
            "password1": "Password:",
            "password2": "Password Confirmation:",
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-control"
            })
        self.fields["password1"].label = "Password:"
        self.fields["password2"].label = "Confirm Password:"
        
        self.fields["email"].required = True
        
    def clean_email(self):
        return self.cleaned_data["email"].lower()


class StyledLoginForm(AuthenticationForm):        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-control"
            })

        self.fields["username"].label = "Email:"
        self.fields["password"].label = "Password:"
        
    def clean_username(self):
        return self.cleaned_data["username"].lower()
    
    
class UserEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-control"
            })
            
        self.fields['email'].required = True
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            ]
        
        labels = {
            'first_name': 'First Name:',
            'last_name': 'Last Name:',
            'email': 'Email Address:',
        }
        
class ProfileEditForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-control"
            })
            
        self.fields['blurb'].widget.attrs.update({
            'rows': '3',
            'maxlength': '140'
            })
            
        self.fields['about_me'].widget.attrs.update({
            'maxlength': '2000'
            })
        
        self.fields['is_public'].widget.attrs.update({
            'class': 'form-check-input'
            })
    
    class Meta:
        model = Profile
        fields = ['blurb',
                  'about_me',
                  'location',
                  'pronouns',
                  'website',
                  'favorite_genre',
                  'favorite_author',
                  'recommend_to_everyone',
                  'currently_reading',
                  'is_public',
                  ]
    
        labels = {'blurb': 'Blurb:',
                  'about_me': 'Biography:',
                  'location': 'Location:',
                  'pronouns': 'Pronouns:',
                  'website': 'Website:',
                  'favorite_genre': 'Favorite Genre:',
                  'favorite_author': 'Favorite Author:',
                  'recommend_to_everyone': 'Everyone should read once:',
                  'currently_reading': 'Currently Reading:',
                  'is_public': 'Public Profile Page:',
                  }
    