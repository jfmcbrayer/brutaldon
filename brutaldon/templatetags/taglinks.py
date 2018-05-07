from django import template
from bs4 import BeautifulSoup
from urllib import parse
from django.urls import reverse

register = template.Library()

@register.filter
def relink_tags(value):
    '''Treat the text as html, and replace tag links with app-internal tag links

    Currently, this only works for tags in toots coming from Mastodon servers,
    not necessarily GNU Social, Pleroma, or other fediverse servers, because
    it relies on the markup that Mastodon puts on tags.

    FIXME: handle arbitrary tag lengths.
    '''
    soup = BeautifulSoup(value, 'html.parser')
    for link in soup.find_all('a', class_='hashtag'):
        link['href'] = reverse('tag', args=[link.span.string])
    return soup.decode(formatter=None)

@register.filter
def relink_toot(value):
    return relink_tags(value)
