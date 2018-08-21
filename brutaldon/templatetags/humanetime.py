from datetime import datetime, timedelta
from django.utils.timezone import get_default_timezone, get_current_timezone, make_naive
from django import template

register = template.Library()

@register.filter(is_safe=True)
def humane_time(arg):
    '''Returns a time string that is humane but not relative (unlike Django's humanetime)

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

    '''
    now = datetime.now()
    arg = make_naive(arg, timezone=get_current_timezone())
    diff = now - arg

    if diff < timedelta(hours=6):
        return arg.strftime("%a, %b %d, %Y at %I:%M %p")
    elif diff < timedelta(hours=12):
        return arg.strftime("%a, %b %d, %Y around %I %p")
    elif diff < timedelta(days=2):
        return arg.strftime("%a, %b %d, %Y in the ") + time_of_day(arg.hour)
    elif diff < timedelta(days=6*28):
        return arg.strftime("%b %d, %Y")
    elif diff < timedelta(days=10*365):
        return arg.strftime("%b, %Y")
    else:
        return arg.strftime("%Y")

def time_of_day(hour):
    """Return a description of what time of day an hour is.

    This is very english-centric and probably not translatable.
    """
    if hour < 3:
        return "wee hours"
    elif hour < 6:
        return "early morning"
    elif hour < 12:
        return "morning"
    elif hour < 18:
        return "afternoon"
    elif hour < 22:
        return "evening"
    else:
        return "night"
