from django import template
from bs4 import BeautifulSoup
from urllib import parse
from django.urls import reverse
from django.utils.translation import gettext as _
from pdb import set_trace

register = template.Library()


@register.filter
def pdb(element):
    set_trace()
    return element


@register.filter
def relink_tags(value):
    """Treat the text as html, and replace tag links with app-internal tag links

    Currently, this only works for tags in toots coming from Mastodon servers,
    not necessarily GNU Social, Pleroma, or other fediverse servers, because
    it relies on the markup that Mastodon puts on tags.

    FIXME: handle arbitrary tag links
    """
    value = value.replace("&apos;", "'")
    soup = BeautifulSoup(value, "html.parser")
    for link in soup.find_all("a", class_="hashtag"):
        try:
            link["href"] = reverse("tag", args=[link.span.string])
        except:
            continue
    return soup.decode(formatter="html")


@register.filter
def relink_mentions(value):
    """Treat the text as html, and replace mention links with app-internal links

    Currently, this only works for mentions in toots coming from Mastodon servers,
    not necessarily GNU Social, Pleroma, or other fediverse servers, because
    it relies on the markup that Mastodon puts on mentions.

    FIXME: handle arbitrary mention links
    """
    value = value.replace("&apos;", "'")
    soup = BeautifulSoup(value, "html.parser")
    for link in soup.find_all("a", class_="mention"):
        parsed = parse.urlparse(link["href"])
        try:
            instance = parsed[1]
            user = parsed[2][2:]
            link["href"] = reverse("user", args=[user + "@" + instance])
        except:
            continue
    return soup.decode(formatter="html")


@register.filter
def relink_toot(value):
    return relink_tags(relink_mentions(value))


@register.filter
def localuser(value):
    """Convert a remote user link to local"""
    try:
        parsed = parse.urlparse(value)
        instance = parsed[1]
        if parsed[2].startswith("/@"):
            user = parsed[2][2:]
        else:
            user = parsed[2].split("/")[-1]
        local = reverse("user", args=[user + "@" + instance])
    except:
        local = value
    return local


@register.filter
def fix_emojos(value, emojos):
    """Replace instances of recognized custom emoji :shortcodes: in value with image link tags
    """
    for emojo in emojos:
        try:
            value = value.replace(
                ":%(shortcode)s:" % emojo,
                '<img src="%(url)s" title=":%(shortcode)s:" alt=":%(shortcode)s:" class="emoji">'
                % emojo,
            )
        except:
            continue
    return value
