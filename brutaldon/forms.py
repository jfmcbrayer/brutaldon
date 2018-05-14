from django import forms

PRIVACY_CHOICES = (('public', 'Public'),
                   ('unlisted', 'Unlisted'),
                   ('private', 'Private'),
                   ('direct', 'Direct'))


class LoginForm(forms.Form):
    instance = forms.CharField(label="Instance",
                               max_length=256)
    username = forms.CharField(label="Email",
                               max_length=256)
    password = forms.CharField(widget=forms.PasswordInput())

class OAuthLoginForm(forms.Form):
    instance = forms.CharField(label="Instance",
                               max_length=256)

class SettingsForm(forms.Form):
    fullbrutalism = forms.BooleanField(label="Use FULLBRUTALISM mode?",
                                       required=False,
                                       help_text=
    """FULLBRUTALISM mode strips away most of the niceties of modern web design when
    brutaldon is viewed in a graphical browser. It has no effect in text-only browsers.""")


class PostForm(forms.Form):
    """def status_post(self, status, in_reply_to_id=None, media_ids=None,
sensitive=False, visibility=None, spoiler_text=None):"""
    status = forms.CharField(label="Toot", max_length=500, widget=forms.Textarea)
    visibility = forms.ChoiceField(label="Toot visibility", choices=PRIVACY_CHOICES)
    spoiler_text = forms.CharField(label="CW or Subject", max_length=500,
                                   required=False)
    media_file_1 = forms.FileField(label = "Media attachment 1",
                                   required=False)
    media_text_1 = forms.CharField(label="Describe media attachment 1.", max_length=500,
                                   required=False)
    media_file_2 = forms.FileField(label = "Media attachment 2",
                                   required=False)
    media_text_2 = forms.CharField(label="Describe media attachment 2.", max_length=500,
                                   required=False)
    media_file_3 = forms.FileField(label = "Media attachment 3",
                                   required=False)
    media_text_3 = forms.CharField(label="Describe media attachment 3.", max_length=500,
                                   required=False)
    media_file_4 = forms.FileField(label = "Media attachment 4",
                                   required=False)
    media_text_4 = forms.CharField(label="Describe media attachment 4.", max_length=500,
                                   required=False)
    media_sensitive = forms.BooleanField(label="Sensitive media?", required=False)

