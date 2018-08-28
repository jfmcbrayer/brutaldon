from django import forms
from django.conf import settings
from pytz import common_timezones
from .models import Theme, Preference


PRIVACY_CHOICES = (('public', 'Public'),
                   ('unlisted', 'Unlisted'),
                   ('private', 'Private'),
                   ('direct', 'Direct'))

timezones = [ (tz, tz) for tz in common_timezones]

MAX_LENGTH = settings.TOOT_MAX_LENGTH

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
        fields = ['theme', 'filter_replies', 'filter_boosts', 'timezone']

class PostForm(forms.Form):
    """def status_post(self, status, in_reply_to_id=None, media_ids=None,
                       sensitive=False, visibility=None, spoiler_text=None):"""
    status = forms.CharField(label="Toot", max_length=MAX_LENGTH, widget=forms.Textarea)
    visibility = forms.ChoiceField(label="Toot visibility", choices=PRIVACY_CHOICES,
                                   required=False)
    spoiler_text = forms.CharField(label="CW or Subject", max_length=MAX_LENGTH,
                                   required=False)
    media_file_1 = forms.FileField(label = "Media 1",
                                   required=False)
    media_text_1 = forms.CharField(label="Describe media 1.",
                                   max_length=MAX_LENGTH,
                                   required=False)
    media_file_2 = forms.FileField(label = "Media 2",
                                   required=False)
    media_text_2 = forms.CharField(label="Describe media 2.",
                                   max_length=MAX_LENGTH,
                                   required=False)
    media_file_3 = forms.FileField(label = "Media 3",
                                   required=False)
    media_text_3 = forms.CharField(label="Describe media 3.",
                                   max_length=MAX_LENGTH,
                                   required=False)
    media_file_4 = forms.FileField(label = "Media 4",
                                   required=False)
    media_text_4 = forms.CharField(label="Describe media 4.",
                                   max_length=MAX_LENGTH,
                                   required=False)
    media_sensitive = forms.BooleanField(label="Sensitive media?", required=False)

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        spoiler_text = cleaned_data.get("spoiler_text")

        if (status and spoiler_text and len(status) + len(spoiler_text) > MAX_LENGTH):
            raise forms.ValidationError("Max length of toot exceeded: %(max_length)s",
                                        code="too_long",
                                        params={"max_length": MAX_LENGTH})
