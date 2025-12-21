from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django import forms
from turnstile.fields import TurnstileField


class RegisterNewUser(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
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


class StyledLoginForm(AuthenticationForm):        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs.update({
                "class": "form-control"
            })

        self.fields["username"].label = "Username:"
        self.fields["password"].label = "Password:"