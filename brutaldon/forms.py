from django import forms

class LoginForm(forms.Form):
    instance = forms.CharField(label="Instance",
                               max_length=256)
    username = forms.CharField(label="Username",
                               max_length=256)
    password = forms.CharField(widget=forms.PasswordInput())

