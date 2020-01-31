from django.urls import reverse


def bookmarklet_url(request):
    share_url = request.build_absolute_uri(reverse("share"))
    return {
        "bookmarklet_url": f"javascript:location.href='{share_url}?url='+encodeURIComponent(location.href)+';title='+encodeURIComponent(document.title)"
    }
