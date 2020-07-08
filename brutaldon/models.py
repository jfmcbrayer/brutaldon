from django.db import models
from django.conf import settings
from django.utils.translation import gettext as _
from pytz import common_timezones

timezones = [(tz, tz) for tz in common_timezones]


class Client(models.Model):
    name = models.CharField(default="brutaldon", max_length=80)
    api_base_id = models.URLField(default="https://mastodon.social")
    version = models.CharField(default="1.0", max_length=80)
    client_id = models.CharField(null=True, blank=True, max_length=2048)
    client_secret = models.CharField(null=True, blank=True, max_length=2048)

    def __str__(self):
        return self.name + ": " + self.api_base_id


class Theme(models.Model):
    name = models.CharField(max_length=80, unique=True)
    prefix = models.CharField(max_length=40, null=True, default="default")
    main_css = models.CharField(
        max_length=1024, blank=True, null=True, default="css/fullbrutalism.css"
    )
    tweaks_css = models.CharField(max_length=1024, blank=True, null=True)
    is_brutalist = models.BooleanField(default=False)

    def __str__(self):
        return self.name


from django.db.models.fields.related_descriptors import ForeignKeyDeferredAttribute


def set_fields(klass):
    fields = []
    for n in dir(klass):
        assert n != "_fields"
        v = getattr(klass, n)
        if not hasattr(v, "field"):
            continue
        if not isinstance(v.field, models.Field):
            continue
        if isinstance(v, ForeignKeyDeferredAttribute):
            continue
        fields.append(n)
    setattr(klass, "_fields", fields)
    return klass


@set_fields
class Preference(models.Model):
    theme = models.ForeignKey(Theme, models.CASCADE, null=False, default=1)
    filter_replies = models.BooleanField(default=False)
    filter_boosts = models.BooleanField(default=False)
    timezone = models.CharField(
        max_length=80, blank=True, null=True, choices=timezones, default="UTC"
    )
    preview_sensitive = models.BooleanField(
        default=False, help_text=_('Show preview for media marked as "sensitive"')
    )

    no_javascript = models.BooleanField(
        default=False,
        help_text=_(
            """Disable all JavaScript. Overrides all other JavaScript options."""
        ),
    )
    notifications = models.BooleanField(
        default=True, help_text=_("""Display live notifications in header.""")
    )
    click_to_load = models.BooleanField(
        default=False,
        help_text=_(
            """Click to load more toots in the same page, rather than using pagination."""
        ),
    )
    lightbox = models.BooleanField(
        default=False, help_text=_("""Use a JavaScript lightbox to display media.""")
    )
    poll_frequency = models.IntegerField(
        default=300,
        help_text=_(
            """Number of seconds to wait between checking notifications. Default: 300"""
        ),
    )
    filter_notifications = models.BooleanField(
        default=False,
        help_text=_("""Exclude boosts and favs from your notifications."""),
    )
    bundle_notifications = models.BooleanField(
        default=False,
        help_text=_(
            """Collapse together boosts or likes of the same toot in the notifications page."""
        ),
    )


class Account(models.Model):
    username = models.EmailField(unique=True)
    email = models.EmailField(null=True, blank=True)
    django_user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, null=True)
    access_token = models.CharField(null=True, blank=True, max_length=2048)
    client = models.ForeignKey(Client, models.SET_NULL, null=True)
    preferences = models.ForeignKey(Preference, models.SET_NULL, null=True)
    note_seen = models.CharField(null=True, blank=True, max_length=128)
