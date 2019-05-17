from datetime import datetime, timedelta
from django.utils.timezone import get_default_timezone, get_current_timezone, localtime
from django.utils.timezone import now as django_now
from django.utils.translation import gettext as _
from django import template

register = template.Library()


@register.filter(is_safe=True)
def humane_time(arg):
    """Returns a time string that is humane but not relative (unlike Django's humanetime)

    For times less than 6 hours ago: display date and time to the minute.
    For times less than 12 hours ago: display date and time to the hour.
    For times more than 12 hours ago display date and "time of day".
    For times more than 2 days ago display date.
    For times more than 6 months ago, display month and year.
    For times more than 10 years ago, display year.

    Prefer words to numbers, unless it is too long.

    The goal is a date/time that is always accurate no matter how long it's
    been sitting there waiting for you to look at it, but is only precise
    to a degree you are liable to care about.

    It is not safe to use on future times.

    FIXME: work out how best to make these strings translatable

    """
    now = django_now()
    arg = localtime(arg)
    diff = now - arg

    if arg.tzinfo == now.tzinfo:
        utc = " (UTC)"
    else:
        utc = ""
    if diff < timedelta(hours=6):
        return arg.strftime("%a, %b %d, %Y at %I:%M %p") + utc
    elif diff < timedelta(hours=12):
        return arg.strftime("%a, %b %d, %Y around %I %p") + utc
    elif diff < timedelta(hours=36):
        return arg.strftime("%a, %b %d, %Y in the ") + time_of_day(arg.hour) + utc
    elif diff < timedelta(days=6 * 28):
        return arg.strftime("%b %d, %Y")
    elif diff < timedelta(days=10 * 365):
        return arg.strftime("%b, %Y")
    else:
        return arg.strftime("%Y")


def time_of_day(hour):
    """Return a description of what time of day an hour is.

    This is very english-centric and probably not translatable.
    """
    if hour < 3:
        return _("wee hours")
    elif hour < 6:
        return _("early morning")
    elif hour < 12:
        return _("morning")
    elif hour < 18:
        return _("afternoon")
    elif hour < 22:
        return _("evening")
    else:
        return _("night")
