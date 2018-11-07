from django import forms
from django.conf import settings
from django.utils.translation import gettext as _
from pytz import common_timezones
from .models import Theme, Preference


PRIVACY_CHOICES = (('public', _('Public')),
                   ('unlisted', _('Unlisted')),
                   ('private', _('Private')),
                   ('direct', _('Direct')))

timezones = [ (tz, tz) for tz in common_timezones]

class LoginForm(forms.Form):
    instance = forms.CharField(label=_("Instance"),
                               max_length=256)
    email = forms.EmailField(label=_("Email"))
    password = forms.CharField(widget=forms.PasswordInput())

class OAuthLoginForm(forms.Form):
    instance = forms.CharField(label=_("Instance"),
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
    visibility = forms.ChoiceField(label=_("Toot visibility"), choices=PRIVACY_CHOICES,
                                   required=False)
    spoiler_text = forms.CharField(label=_("CW or Subject"),
                                   required=False)
    media_file_1 = forms.FileField(label = _("Media 1"),
                                   required=False)
    media_text_1 = forms.CharField(label=_("Describe media 1."),
                                   required=False)
    media_file_2 = forms.FileField(label = _("Media 2"),
                                   required=False)
    media_text_2 = forms.CharField(label=_("Describe media 2."),
                                   required=False)
    media_file_3 = forms.FileField(label = _("Media 3"),
                                   required=False)
    media_text_3 = forms.CharField(label=_("Describe media 3."),
                                   required=False)
    media_file_4 = forms.FileField(label = _("Media 4"),
                                   required=False)
    media_text_4 = forms.CharField(label=_("Describe media 4."),
                                   required=False)
    media_sensitive = forms.BooleanField(label=_("Sensitive media?"), required=False)
