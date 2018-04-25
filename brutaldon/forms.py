from django import forms

class LoginForm(forms.Form):
    instance = forms.CharField(label="Instance",
                               max_length=256)
    username = forms.CharField(label="Email",
                               max_length=256)
    password = forms.CharField(widget=forms.PasswordInput())

class SettingsForm(forms.Form):
    fullbrutalism = forms.BooleanField(label="Use FULLBRUTALISM mode?",
                                       required=False,
                                       help_text=
    """FULLBRUTALISM mode strips away most of the niceties of modern web design when
    brutaldon is viewed in a graphical browser. It has no effect in text-only browsers.""")

    
