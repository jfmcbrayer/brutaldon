from django import forms
from django.conf import settings
from pytz import common_timezones
from .models import Theme, Preference


PRIVACY_CHOICES = (('public', 'Public'),
                   ('unlisted', 'Unlisted'),
                   ('private', 'Private'),
                   ('direct', 'Direct'))

timezones = [ (tz, tz) for tz in common_timezones]

class LoginForm(forms.Form):
    instance = forms.CharField(label="Instance",
                               max_length=256)
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput())

class OAuthLoginForm(forms.Form):
    instance = forms.CharField(label="Instance",
                               max_length=256)

class PreferencesForm(forms.ModelForm):
    class Meta:
        model = Preference
        fields = ['theme', 'filter_replies', 'filter_boosts', 'timezone',
                  'no_javascript', 'notifications', 'click_to_load', 'lightbox', 'poll_frequency']

class PostForm(forms.Form):
    """def status_post(self, status, in_reply_to_id=None, media_ids=None,
                       sensitive=False, visibility=None, spoiler_text=None):"""
    status = forms.CharField(label="Toot", widget=forms.Textarea)
    visibility = forms.ChoiceField(label="Toot visibility", choices=PRIVACY_CHOICES,
                                   required=False)
    spoiler_text = forms.CharField(label="CW or Subject",
                                   required=False)
    media_file_1 = forms.FileField(label = "Media 1",
                                   required=False)
    media_text_1 = forms.CharField(label="Describe media 1.",
                                   required=False)
    media_file_2 = forms.FileField(label = "Media 2",
                                   required=False)
    media_text_2 = forms.CharField(label="Describe media 2.",
                                   required=False)
    media_file_3 = forms.FileField(label = "Media 3",
                                   required=False)
    media_text_3 = forms.CharField(label="Describe media 3.",
                                   required=False)
    media_file_4 = forms.FileField(label = "Media 4",
                                   required=False)
    media_text_4 = forms.CharField(label="Describe media 4.",
                                   required=False)
    media_sensitive = forms.BooleanField(label="Sensitive media?", required=False)
