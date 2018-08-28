from django.db import models
from django.conf import settings
from pytz import common_timezones

timezones = [(tz, tz) for tz in common_timezones]

class Client(models.Model):
    name = models.CharField(default = "brutaldon", max_length=80)
    api_base_id = models.URLField(default="https://mastodon.social")
    client_id = models.CharField(null=True, blank=True, max_length=2048)
    client_secret = models.CharField(null=True, blank=True, max_length=2048)

    def __str__(self):
        return self.name + ": " + self.api_base_id

class Theme(models.Model):
    name = models.CharField(max_length=80, unique=True)
    prefix = models.CharField(max_length=40, null=True, default="default")
    main_css = models.CharField(max_length=1024, blank=True, null=True,
                                default="css/fullbrutalism.css")
    tweaks_css = models.CharField(max_length=1024, blank=True, null=True)
    is_brutalist = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Preference(models.Model):
    theme = models.ForeignKey(Theme, models.CASCADE, null=False, default=1)
    filter_replies = models.BooleanField(default=False)
    filter_boosts = models.BooleanField(default=False)
    timezone = models.CharField(max_length=80, blank=True, null=True,
                                choices=timezones, default='UTC')

class Account(models.Model):
    username = models.EmailField(unique=True)
    email = models.EmailField(null=True, blank=True)
    django_user = models.ForeignKey(settings.AUTH_USER_MODEL, models.CASCADE, null=True)
    access_token = models.CharField(null=True, blank=True, max_length=2048)
    client= models.ForeignKey(Client, models.SET_NULL, null=True)
    preferences = models.ForeignKey(Preference, models.SET_NULL, null=True)

