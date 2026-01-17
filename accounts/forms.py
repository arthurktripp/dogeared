from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from turnstile.fields import TurnstileField

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