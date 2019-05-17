from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.db import IntegrityError
from django.conf import settings as django_settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache, cache_page
from django.urls import reverse
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.utils.translation import gettext as _
from brutaldon.forms import (
    LoginForm,
    OAuthLoginForm,
    PreferencesForm,
    PostForm,
    FilterForm,
)
from brutaldon.models import Client, Account, Preference, Theme
from mastodon import (
    Mastodon,
    AttribAccessDict,
    MastodonError,
    MastodonAPIError,
    MastodonNotFoundError,
)
from urllib import parse
from pdb import set_trace
from inscriptis import get_text
from time import sleep
import re


class NotLoggedInException(Exception):
    pass


###
### Utility functions
###


def get_usercontext(request):
    if is_logged_in(request):
        try:
            client = Client.objects.get(api_base_id=request.session["active_instance"])
            user = Account.objects.get(username=request.session["active_username"])
        except (
            Client.DoesNotExist,
            Client.MultipleObjectsReturned,
            Account.DoesNotExist,
            Account.MultipleObjectsReturned,
        ):
            raise NotLoggedInException()
        mastodon = Mastodon(
            client_id=client.client_id,
            client_secret=client.client_secret,
            access_token=user.access_token,
            api_base_url=client.api_base_id,
            ratelimit_method="throw",
        )
        return user, mastodon
    else:
        return None, None


def is_logged_in(request):
    return request.session.has_key("active_user")


def _notes_count(account, mastodon):
    if not mastodon:
        return ""
    notes = mastodon.notifications(limit=40)
    if account.preferences.filter_notifications:
        notes = [
            note for note in notes if note.type == "mention" or note.type == "follow"
        ]
    for index, item in enumerate(notes):
        if account.note_seen is None:
            account.note_seen = "0"
            account.save()
        if str(item.id) <= str(account.note_seen):
            break
    else:
        index = "40+"
    return str(index)


def br_login_required(function=None, home_url=None, redirect_field_name=None):
    """Check that the user is logged in to a Mastodon instance.

    This decorator ensures that the view functions it is called on can be
    accessed only by logged in users. When an instanceless user accesses
    such a protected view, they are redirected to the address specified in
    the field named in `next_field` or, lacking such a value, the URL in
    `home_url`, or the `ANONYMOUS_HOME_URL` setting.
    """
    if home_url is None:
        home_url = django_settings.ANONYMOUS_HOME_URL

    def _dec(view_func):
        def _view(request, *args, **kwargs):
            if not is_logged_in(request):
                url = None
                if redirect_field_name and redirect_field_name in request.REQUEST:
                    url = request.REQUEST[redirect_field_name]
                if not url:
                    url = home_url
                if not url:
                    url = "/"
                return HttpResponseRedirect(url)
            else:
                return view_func(request, *args, **kwargs)

        _view.__name__ = view_func.__name__
        _view.__dict__ = view_func.__dict__
        _view.__doc__ = view_func.__doc__

        return _view

    if function is None:
        return _dec
    else:
        return _dec(function)


def user_search(request):
    check = request.POST.get("status", "").split()
    if len(check):
        check = check[-1]
        if len(check) > 1 and check.startswith("@"):
            check = check[1:]
            return user_search_inner(request, check)
        else:
            check = "&nbsp;"
    else:
        check = "&nbsp;"
    return HttpResponse(check)


def user_search_inner(request, query):
    account, mastodon = get_usercontext(request)
    results = mastodon.search(query)
    return render(
        request,
        "intercooler/users.html",
        {
            "active_users": "\n".join([user.acct for user in results.accounts]),
            "preferences": account.preferences,
        },
    )


def timeline(
    request,
    timeline="home",
    timeline_name="Home",
    max_id=None,
    min_id=None,
    filter_context="home",
):
    account, mastodon = get_usercontext(request)
    data = mastodon.timeline(timeline, limit=40, max_id=max_id, min_id=min_id)
    form = PostForm(
        initial={"visibility": request.session["active_user"].source.privacy}
    )
    try:
        prev = data[0]._pagination_prev
        if len(mastodon.timeline(min_id=prev["min_id"])) == 0:
            prev = None
        else:
            prev["min_id"] = data[0].id
    except (IndexError, AttributeError, KeyError):
        prev = None
    try:
        next = data[-1]._pagination_next
        next["max_id"] = data[-1].id
    except (IndexError, AttributeError, KeyError):
        next = None

    notifications = _notes_count(account, mastodon)
    filters = get_filters(mastodon, filter_context)

    # This filtering has to be done *after* getting next/prev links
    if account.preferences.filter_replies:
        data = [x for x in data if not x.in_reply_to_id]
    if account.preferences.filter_boosts:
        data = [x for x in data if not x.reblog]

    # Apply filters
    data = [x for x in data if not toot_matches_filters(x, filters)]

    return render(
        request,
        "main/%s_timeline.html" % timeline,
        {
            "toots": data,
            "form": form,
            "timeline": timeline,
            "timeline_name": timeline_name,
            "own_acct": request.session["active_user"],
            "preferences": account.preferences,
            "notifications": notifications,
            "prev": prev,
            "next": next,
        },
    )


def get_filters(mastodon, context=None):
    try:
        if context:
            return [ff for ff in mastodon.filters() if context in ff.context]
        else:
            return mastodon.filters()
    except:
        return []


def toot_matches_filters(toot, filters=[]):
    if not filters:
        return False

    def maybe_rewrite_filter(filter):
        if filter.whole_word:
            return f"\\b{filter.phrase}\\b"
        else:
            return filter.phrase

    phrases = [maybe_rewrite_filter(x) for x in filters]
    pattern = "|".join(phrases)
    try:
        if toot.get("type") in ["reblog", "favourite"]:
            return re.search(
                pattern, toot.status.spoiler_text + toot.status.content, re.I
            )
        return re.search(pattern, toot.spoiler_text + toot.content, re.I)
    except:
        return False


def switch_accounts(request, new_account):
    """Try to switch accounts to the specified account, if it is already in
    the user's session. Sets up new session variables. Returns boolean success
    code."""
    accounts_dict = request.session.get("accounts_dict")
    if not accounts_dict or not new_account in accounts_dict.keys():
        return False
    try:
        account = Account.objects.get(id=accounts_dict[new_account]["account_id"])
        if account.username != new_account:
            return False
    except Account.DoesNotExist:
        return False
    request.session["active_user"] = accounts_dict[new_account]["user"]
    request.session["active_username"] = account.username
    request.session["active_instance"] = account.client.api_base_id
    return True


def forget_account(request, account_name):
    """Forget that you were logged into an account. If it's the last one, log out
    entirely. Sets up session variables. Returns a redirect to the correct
    view.
    """
    accounts_dict = request.session.get("accounts_dict")
    if not accounts_dict or not account_name in accounts_dict.keys():
        return redirect("accounts")
    del accounts_dict[account_name]
    if len(accounts_dict) == 0:
        request.session.flush()
        return redirect("about")
    elif account_name == request.session["active_username"]:
        key = [*accounts_dict][0]
        if switch_accounts(request, key):
            return redirect("accounts")
        else:
            request.session.flush()
            return redirect("about")
    else:
        request.session["accounts_dict"] = accounts_dict
        return redirect("accounts")


###
### View functions
###


def notes_count(request):
    account, mastodon = get_usercontext(request)
    count = _notes_count(account, mastodon)
    return render(
        request,
        "intercooler/notes.html",
        {"notifications": count, "preferences": account.preferences},
    )


@br_login_required
def home(request, next=None, prev=None):
    return timeline(
        request, "home", "Home", max_id=next, min_id=prev, filter_context="home"
    )


@br_login_required
def local(request, next=None, prev=None, filter_context="public"):
    return timeline(request, "local", "Local", max_id=next, min_id=prev)


@br_login_required
def fed(request, next=None, prev=None, filter_context="public"):
    return timeline(request, "public", "Federated", max_id=next, min_id=prev)


@br_login_required
def tag(request, tag):
    try:
        account, mastodon = get_usercontext(request)
    except NotLoggedInException:
        return redirect(login)
    data = mastodon.timeline_hashtag(tag)
    notifications = _notes_count(account, mastodon)
    return render(
        request,
        "main/timeline.html",
        {
            "toots": data,
            "timeline_name": "#" + tag,
            "own_acct": request.session["active_user"],
            "notifications": notifications,
            "preferences": account.preferences,
        },
    )


@never_cache
def login(request):
    # User posts instance name in form.
    # POST page redirects user to instance, where they log in.
    # Instance redirects user to oauth_after_login view.
    # oauth_after_login view saves credential in session, then redirects to home.
    if request.method == "GET":
        form = OAuthLoginForm()
        return render(request, "setup/login-oauth.html", {"form": form})
    elif request.method == "POST":
        form = OAuthLoginForm(request.POST)
        redirect_uris = request.build_absolute_uri(reverse("oauth_callback"))
        if form.is_valid():
            api_base_url = form.cleaned_data["instance"]
            tmp_base = parse.urlparse(api_base_url.lower())
            if tmp_base.netloc == "":
                api_base_url = parse.urlunparse(
                    ("https", tmp_base.path, "", "", "", "")
                )
                request.session["active_instance_hostname"] = tmp_base.path
            else:
                api_base_url = api_base_url.lower()
                request.session["active_instance_hostname"] = tmp_base.netloc

            request.session["active_instance"] = api_base_url
            try:
                client = Client.objects.get(api_base_id=api_base_url)
            except (Client.DoesNotExist, Client.MultipleObjectsReturned):
                (client_id, client_secret) = Mastodon.create_app(
                    "brutaldon",
                    api_base_url=api_base_url,
                    redirect_uris=redirect_uris,
                    scopes=["read", "write", "follow"],
                )
                client = Client(
                    api_base_id=api_base_url,
                    client_id=client_id,
                    client_secret=client_secret,
                )
                client.save()

            request.session["active_client_id"] = client.client_id
            request.session["active_client_secret"] = client.client_secret

            mastodon = Mastodon(
                client_id=client.client_id,
                client_secret=client.client_secret,
                api_base_url=api_base_url,
            )
            client.version = mastodon.instance().get("version")
            client.save()
            return redirect(
                mastodon.auth_request_url(
                    redirect_uris=redirect_uris, scopes=["read", "write", "follow"]
                )
            )
        else:
            return render(request, "setup/login.html", {"form": form})

    else:
        return redirect(login)


@never_cache
def oauth_callback(request):
    code = request.GET.get("code", "")
    mastodon = Mastodon(
        client_id=request.session["active_client_id"],
        client_secret=request.session["active_client_secret"],
        api_base_url=request.session["active_instance"],
    )
    redirect_uri = request.build_absolute_uri(reverse("oauth_callback"))
    access_token = mastodon.log_in(
        code=code, redirect_uri=redirect_uri, scopes=["read", "write", "follow"]
    )
    request.session["access_token"] = access_token
    user = mastodon.account_verify_credentials()
    try:
        account = Account.objects.get(
            username=user.username + "@" + request.session["active_instance_hostname"]
        )
        account.access_token = access_token
        if not account.preferences:
            preferences = Preference(theme=Theme.objects.get(id=1))
            preferences.save()
            account.preferences = preferences
        else:
            request.session["timezone"] = account.preferences.timezone
        account.save()
    except (Account.DoesNotExist, Account.MultipleObjectsReturned):
        preferences = Preference(theme=Theme.objects.get(id=1))
        preferences.save()
        account = Account(
            username=user.username + "@" + request.session["active_instance_hostname"],
            access_token=access_token,
            client=Client.objects.get(api_base_id=request.session["active_instance"]),
            preferences=preferences,
        )
        account.save()

    request.session["active_user"] = user
    request.session["active_username"] = (
        user.username + "@" + request.session["active_instance_hostname"]
    )

    accounts_dict = request.session.get("accounts_dict")
    if not accounts_dict:
        accounts_dict = {}
    accounts_dict[account.username] = {"account_id": account.id, "user": user}
    request.session["accounts_dict"] = accounts_dict

    return redirect(home)


@never_cache
def old_login(request):
    if request.method == "GET":
        form = LoginForm()
        return render(request, "setup/login.html", {"form": form})
    elif request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            api_base_url = form.cleaned_data["instance"]
            tmp_base = parse.urlparse(api_base_url.lower())
            if tmp_base.netloc == "":
                api_base_url = parse.urlunparse(
                    ("https", tmp_base.path, "", "", "", "")
                )
                request.session["active_instance_hostname"] = tmp_base.path
            else:
                api_base_url = api_base_url.lower()
                request.session["active_instance_hostname"] = tmp_base.netloc

            request.session["active_instance"] = api_base_url
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            try:
                client = Client.objects.get(api_base_id=api_base_url)
            except (Client.DoesNotExist, Client.MultipleObjectsReturned):
                (client_id, client_secret) = Mastodon.create_app(
                    "brutaldon",
                    api_base_url=api_base_url,
                    scopes=["read", "write", "follow"],
                )
                client = Client(
                    api_base_id=api_base_url,
                    client_id=client_id,
                    client_secret=client_secret,
                )
                client.save()

            mastodon = Mastodon(
                client_id=client.client_id,
                client_secret=client.client_secret,
                api_base_url=api_base_url,
            )
            client.version = mastodon.instance().get("version")
            client.save()

            try:
                account = Account.objects.get(email=email, client_id=client.id)
            except (Account.DoesNotExist, Account.MultipleObjectsReturned):
                preferences = Preference(theme=Theme.objects.get(id=1))
                preferences.save()
                account = Account(
                    email=email, access_token="", client=client, preferences=preferences
                )
            try:
                access_token = mastodon.log_in(
                    email, password, scopes=["read", "write", "follow"]
                )
                account.access_token = access_token
                user = mastodon.account_verify_credentials()
                request.session["active_user"] = user
                request.session["active_username"] = (
                    user.username + "@" + request.session["active_instance_hostname"]
                )
                account.username = request.session["active_username"]
                request.session["timezone"] = account.preferences.timezone

                accounts_dict = request.session.get("accounts_dict")
                if not accounts_dict:
                    accounts_dict = {}
                accounts_dict[account.username] = {
                    "account_id": account.id,
                    "user": user,
                }
                request.session["accounts_dict"] = accounts_dict
                account.save()

                return redirect(home)
            except IntegrityError:
                account = Account.objects.get(username=account.username)
                accounts_dict[account.username] = {
                    "account_id": account.id,
                    "user": user,
                }
                request.session["accounts_dict"] = accounts_dict
                return redirect(home)
            except Exception as ex:
                form.add_error("", ex)
                return render(request, "setup/login.html", {"form": form})
        else:
            return render(request, "setup/login.html", {"form": form})


@never_cache
def logout(request):
    request.session.flush()
    return redirect(about)


def error(request):
    return render(request, "error.html", {"error": _("Not logged in yet.")})


@br_login_required
def note(request, next=None, prev=None):
    try:
        account, mastodon = get_usercontext(request)
    except NotLoggedInException:
        return redirect(about)
    last_seen = mastodon.notifications(limit=1)[0]
    account.note_seen = last_seen.id
    account.save()

    notes = mastodon.notifications(limit=40, max_id=next, min_id=prev)
    filters = get_filters(mastodon, context="notifications")

    if account.preferences.filter_notifications:
        notes = [
            note for note in notes if note.type == "mention" or note.type == "follow"
        ]

    # Apply filters
    notes = [x for x in notes if not toot_matches_filters(x, filters)]

    try:
        prev = notes[0]._pagination_prev
        if len(mastodon.notifications(min_id=prev["min_id"])) == 0:
            prev = None
    except (IndexError, AttributeError, KeyError):
        prev = None
    try:
        next = notes[-1]._pagination_next
    except (IndexError, AttributeError, KeyError):
        next = None
    return render(
        request,
        "main/notifications.html",
        {
            "notes": notes,
            "timeline": "Notifications",
            "timeline_name": "Notifications",
            "own_acct": request.session["active_user"],
            "preferences": account.preferences,
            "prev": prev,
            "next": next,
        },
    )


@br_login_required
def thread(request, id):
    account, mastodon = get_usercontext(request)
    try:
        context = mastodon.status_context(id)
    except MastodonNotFoundError:
        raise Http404(_("Thread not found; the message may have been deleted."))
    toot = mastodon.status(id)
    notifications = _notes_count(account, mastodon)
    filters = get_filters(mastodon, context="thread")

    # Apply filters
    ancestors = [x for x in context.ancestors if not toot_matches_filters(x, filters)]
    descendants = [
        x for x in context.descendants if not toot_matches_filters(x, filters)
    ]

    return render(
        request,
        "main/thread.html",
        {
            "context": context,
            "toot": toot,
            "ancestors": ancestors,
            "descendants": descendants,
            "own_acct": request.session["active_user"],
            "notifications": notifications,
            "preferences": account.preferences,
        },
    )


@br_login_required
def user(request, username, prev=None, next=None):
    try:
        account, mastodon = get_usercontext(request)
    except NotLoggedInException:
        return redirect(about)
    try:
        user_dict = [
            dict
            for dict in mastodon.account_search(username)
            if (
                (dict.acct == username)
                or (
                    dict.acct == username.split("@")[0]
                    and username.split("@")[1] == account.username.split("@")[1]
                )
            )
        ][0]
    except (IndexError, AttributeError):
        raise Http404(_("The user %s could not be found.") % username)
    data = mastodon.account_statuses(user_dict.id, max_id=next, min_id=prev)
    relationship = mastodon.account_relationships(user_dict.id)[0]
    notifications = _notes_count(account, mastodon)
    try:
        prev = data[0]._pagination_prev
        if len(mastodon.account_statuses(user_dict.id, min_id=prev["min_id"])) == 0:
            prev = None
    except (IndexError, AttributeError, KeyError):
        prev = None
    try:
        next = data[-1]._pagination_next
    except (IndexError, AttributeError, KeyError):
        next = None
    return render(
        request,
        "main/user.html",
        {
            "toots": data,
            "user": user_dict,
            "relationship": relationship,
            "own_acct": request.session["active_user"],
            "preferences": account.preferences,
            "notifications": notifications,
            "prev": prev,
            "next": next,
        },
    )


@never_cache
@br_login_required
def settings(request):
    try:
        account, mastodon = get_usercontext(request)
        account.client.version = mastodon.instance().get("version")
        account.client.save()

    except NotLoggedInException:
        return redirect(about)
    if request.method == "POST":
        form = PreferencesForm(request.POST)
        if form.is_valid():
            account.preferences.theme = form.cleaned_data["theme"]
            account.preferences.filter_replies = form.cleaned_data["filter_replies"]
            account.preferences.filter_boosts = form.cleaned_data["filter_boosts"]
            account.preferences.timezone = form.cleaned_data["timezone"]
            account.preferences.no_javascript = form.cleaned_data["no_javascript"]
            account.preferences.notifications = form.cleaned_data["notifications"]
            account.preferences.click_to_load = form.cleaned_data["click_to_load"]
            account.preferences.lightbox = form.cleaned_data["lightbox"]
            account.preferences.filter_notifications = form.cleaned_data[
                "filter_notifications"
            ]
            account.preferences.poll_frequency = form.cleaned_data["poll_frequency"]
            request.session["timezone"] = account.preferences.timezone
            account.preferences.save()
            account.save()

            # Update this here because it's a handy place to do it.
            user_info = mastodon.account_verify_credentials()
            request.session["active_user"] = user_info

            return redirect(home)
        else:
            return render(
                request, "setup/settings.html", {"form": form, "account": account}
            )
    else:
        request.session["timezone"] = account.preferences.timezone
        form = PreferencesForm(instance=account.preferences)
        return render(
            request,
            "setup/settings.html",
            {"form": form, "account": account, "preferences": account.preferences},
        )


@never_cache
@br_login_required
def toot(request, mention=None):
    account, mastodon = get_usercontext(request)
    if request.method == "GET":
        if mention:
            if not mention.startswith("@"):
                mention = "@" + mention
            form = PostForm(
                initial={
                    "visibility": request.session["active_user"].source.privacy,
                    "status": mention + " ",
                }
            )
        else:
            form = PostForm(
                initial={"visibility": request.session["active_user"].source.privacy}
            )
        if request.GET.get("ic-request"):
            return render(
                request,
                "intercooler/post.html",
                {
                    "form": form,
                    "own_acct": request.session["active_user"],
                    "preferences": account.preferences,
                },
            )
        else:
            return render(
                request,
                "main/post.html",
                {
                    "form": form,
                    "own_acct": request.session["active_user"],
                    "preferences": account.preferences,
                },
            )
    elif request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            # create media objects
            media_objects = []
            for index in range(1, 5):
                if "media_file_" + str(index) in request.FILES:
                    media_objects.append(
                        mastodon.media_post(
                            request.FILES[
                                "media_file_" + str(index)
                            ].temporary_file_path(),
                            description=request.POST.get(
                                "media_text_" + str(index), None
                            ),
                        )
                    )
            if form.cleaned_data["visibility"] == "":
                form.cleaned_data["visibility"] = request.session[
                    "active_user"
                ].source.privacy
            try:
                try:
                    mastodon.status_post(
                        status=form.cleaned_data["status"],
                        visibility=form.cleaned_data["visibility"],
                        spoiler_text=form.cleaned_data["spoiler_text"],
                        media_ids=media_objects,
                        content_type="text/markdown",
                    )
                except TypeError:
                    mastodon.status_post(
                        status=form.cleaned_data["status"],
                        visibility=form.cleaned_data["visibility"],
                        spoiler_text=form.cleaned_data["spoiler_text"],
                        media_ids=media_objects,
                    )
            except MastodonAPIError as error:
                form.add_error(
                    "",
                    "%s (%s used)"
                    % (
                        error.args[-1],
                        len(form.cleaned_data["status"])
                        + len(form.cleaned_data["spoiler_text"]),
                    ),
                )
                return render(
                    request,
                    "main/post.html",
                    {
                        "form": form,
                        "own_acct": request.session["active_user"],
                        "preferences": account.preferences,
                    },
                )
            return redirect(home)
        else:
            return render(
                request,
                "main/post.html",
                {
                    "form": form,
                    "own_acct": request.session["active_user"],
                    "preferences": account.preferences,
                },
            )
    else:
        return redirect(toot)


@br_login_required
def redraft(request, id):
    if request.method == "GET":
        account, mastodon = get_usercontext(request)
        toot = mastodon.status(id)
        toot_content = get_text(toot.content)  # convert to plain text
        # fix up white space
        toot_content = re.sub("(^\n)|(\n$)", "", re.sub("\n\n", "\n", toot_content))
        # Fix up references
        for mention in toot.mentions:
            menchie_re = re.compile(r"\s?@" + mention.username + r"\s", re.I)
            toot_content = menchie_re.sub(
                " @" + mention.acct + " ", toot_content, count=1
            )
        form = PostForm(
            {
                "status": toot_content.strip(),
                "visibility": toot.visibility,
                "spoiler_text": toot.spoiler_text,
                "media_text_1": safe_get_attachment(toot, 0).description,
                "media_text_2": safe_get_attachment(toot, 1).description,
                "media_text_3": safe_get_attachment(toot, 2).description,
                "media_text_4": safe_get_attachment(toot, 3).description,
            }
        )
        return render(
            request,
            "main/redraft.html",
            {
                "toot": toot,
                "form": form,
                "redraft": True,
                "own_acct": request.session["active_user"],
                "preferences": account.preferences,
            },
        )
    elif request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        account, mastodon = get_usercontext(request)
        toot = mastodon.status(id)
        if form.is_valid():
            media_objects = []
            for index in range(1, 5):
                if "media_file_" + str(index) in request.FILES:
                    media_objects.append(
                        mastodon.media_post(
                            request.FILES[
                                "media_file_" + str(index)
                            ].temporary_file_path(),
                            description=request.POST.get(
                                "media_text_" + str(index), None
                            ),
                        )
                    )
            if form.cleaned_data["visibility"] == "":
                form.cleaned_data["visibility"] = request.session[
                    "active_user"
                ].source.privacy
            try:
                try:
                    mastodon.status_post(
                        status=form.cleaned_data["status"],
                        visibility=form.cleaned_data["visibility"],
                        spoiler_text=form.cleaned_data["spoiler_text"],
                        media_ids=media_objects,
                        in_reply_to_id=toot.in_reply_to_id,
                        content_type="text/markdown",
                    )
                except TypeError:
                    mastodon.status_post(
                        status=form.cleaned_data["status"],
                        visibility=form.cleaned_data["visibility"],
                        spoiler_text=form.cleaned_data["spoiler_text"],
                        media_ids=media_objects,
                        in_reply_to_id=toot.in_reply_to_id,
                    )
                mastodon.status_delete(id)
            except MastodonAPIError as error:
                form.add_error(
                    "",
                    "%s (%s used)"
                    % (
                        error.args[-1],
                        len(form.cleaned_data["status"])
                        + len(form.cleaned_data["spoiler_text"]),
                    ),
                )
                return render(
                    request,
                    "main/redraft.html",
                    {
                        "toot": toot,
                        "form": form,
                        "redraft": True,
                        "own_acct": request.session["active_user"],
                        "preferences": account.preferences,
                    },
                )
            return redirect(home)
        else:
            return render(
                request,
                "main/redraft.html",
                {
                    "toot": toot,
                    "form": form,
                    "redraft": True,
                    "own_acct": request.session["active_user"],
                    "preferences": account.preferences,
                },
            )
    else:
        return redirect(redraft, id)


def safe_get_attachment(toot, index):
    """Get an attachment from a toot, without crashing if it isn't there."""
    try:
        return toot.media_attachments[index]
    except IndexError:
        adict = AttribAccessDict()
        adict.id, adict.type, adict.description = "", "unknown", ""
        adict.url, adict.remote_url, adict.preview_url = "", "", ""
        adict.text_url = ""
        return adict


@br_login_required
def reply(request, id):
    if request.method == "GET":
        account, mastodon = get_usercontext(request)
        toot = mastodon.status(id)
        context = mastodon.status_context(id)
        notifications = _notes_count(account, mastodon)
        if toot.account.acct != request.session["active_user"].acct:
            initial_text = "@" + toot.account.acct + " "
        else:
            initial_text = ""
        for mention in [
            x
            for x in toot.mentions
            if x.acct != request.session["active_user"].acct
            and x.acct != toot.account.acct
        ]:
            initial_text += "@" + mention.acct + " "
        form = PostForm(
            initial={
                "status": initial_text,
                "visibility": toot.visibility,
                "spoiler_text": toot.spoiler_text,
            }
        )
        return render(
            request,
            "main/reply.html",
            {
                "context": context,
                "toot": toot,
                "form": form,
                "reply": True,
                "own_acct": request.session["active_user"],
                "notifications": notifications,
                "preferences": account.preferences,
            },
        )
    elif request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        account, mastodon = get_usercontext(request)
        toot = mastodon.status(id)
        context = mastodon.status_context(id)
        notifications = _notes_count(account, mastodon)
        if form.is_valid():
            # create media objects
            media_objects = []
            for index in range(1, 5):
                if "media_file_" + str(index) in request.FILES:
                    media_objects.append(
                        mastodon.media_post(
                            request.FILES[
                                "media_file_" + str(index)
                            ].temporary_file_path(),
                            description=request.POST.get(
                                "media_text_" + str(index), None
                            ),
                        )
                    )
            try:
                try:
                    mastodon.status_post(
                        status=form.cleaned_data["status"],
                        visibility=form.cleaned_data["visibility"],
                        spoiler_text=form.cleaned_data["spoiler_text"],
                        media_ids=media_objects,
                        in_reply_to_id=id,
                        content_type="text/markdown",
                    )
                except TypeError:
                    mastodon.status_post(
                        status=form.cleaned_data["status"],
                        visibility=form.cleaned_data["visibility"],
                        spoiler_text=form.cleaned_data["spoiler_text"],
                        media_ids=media_objects,
                        in_reply_to_id=id,
                    )
            except MastodonAPIError as error:
                form.add_error(
                    "",
                    "%s (%s used)"
                    % (
                        error.args[-1],
                        len(form.cleaned_data["status"])
                        + len(form.cleaned_data["spoiler_text"]),
                    ),
                )
                return render(
                    request,
                    "main/reply.html",
                    {
                        "context": context,
                        "toot": toot,
                        "form": form,
                        "reply": True,
                        "own_acct": request.session["active_user"],
                        "notifications": notifications,
                        "preferences": account.preferences,
                    },
                )
            return HttpResponseRedirect(
                reverse("thread", args=[id]) + "#toot-" + str(id)
            )
        else:
            return render(
                request,
                "main/reply.html",
                {
                    "context": context,
                    "toot": toot,
                    "form": form,
                    "reply": True,
                    "own_acct": request.session["active_user"],
                    "preferences": account.preferences,
                },
            )
    else:
        return HttpResponseRedirect(reverse("reply", args=[id]) + "#toot-" + str(id))


@never_cache
@br_login_required
def fav(request, id):
    account, mastodon = get_usercontext(request)
    toot = mastodon.status(id)
    if request.method == "POST":
        if not request.POST.get("cancel", None):
            if toot.favourited:
                mastodon.status_unfavourite(id)
            else:
                mastodon.status_favourite(id)
        if request.POST.get("ic-request"):
            toot["favourited"] = not toot["favourited"]
            return render(
                request,
                "intercooler/fav.html",
                {
                    "toot": toot,
                    "own_acct": request.session["active_user"],
                    "preferences": account.preferences,
                },
            )
        else:
            return HttpResponseRedirect(
                reverse("thread", args=[id]) + "#toot-" + str(id)
            )
    else:
        return render(
            request,
            "main/fav.html",
            {
                "toot": toot,
                "own_acct": request.session["active_user"],
                "confirm_page": True,
                "preferences": account.preferences,
            },
        )


@never_cache
@br_login_required
def boost(request, id):
    account, mastodon = get_usercontext(request)
    toot = mastodon.status(id)
    if request.method == "POST":
        if not request.POST.get("cancel", None):
            if toot.reblogged:
                mastodon.status_unreblog(id)
            else:
                mastodon.status_reblog(id)
        if request.POST.get("ic-request"):
            toot["reblogged"] = not toot["reblogged"]
            return render(
                request,
                "intercooler/boost.html",
                {
                    "toot": toot,
                    "own_acct": request.session["active_user"],
                    "preferences": account.preferences,
                },
            )
        else:
            return HttpResponseRedirect(
                reverse("thread", args=[id]) + "#toot-" + str(id)
            )
    else:
        return render(
            request,
            "main/boost.html",
            {
                "toot": toot,
                "own_acct": request.session["active_user"],
                "confirm_page": True,
                "preferences": account.preferences,
            },
        )


@never_cache
@br_login_required
def delete(request, id):
    account, mastodon = get_usercontext(request)
    toot = mastodon.status(id)
    if request.method == "POST" or request.method == "DELETE":
        if toot.account.acct != request.session["active_user"].acct:
            return redirect("home")
        if not request.POST.get("cancel", None):
            mastodon.status_delete(id)
            if request.POST.get("ic-request"):
                return HttpResponse("")
        return redirect(home)
    else:
        return render(
            request,
            "main/delete.html",
            {
                "toot": toot,
                "own_acct": request.session["active_user"],
                "confirm_page": True,
                "preferences": account.preferences,
            },
        )


@never_cache
@br_login_required
def follow(request, id):
    account, mastodon = get_usercontext(request)
    try:
        user_dict = mastodon.account(id)
        relationship = mastodon.account_relationships(user_dict.id)[0]
    except (IndexError, AttributeError, KeyError):
        raise Http404("The user could not be found.")
    if request.method == "POST":
        if not request.POST.get("cancel", None):
            if relationship.requested or relationship.following:
                mastodon.account_unfollow(id)
            else:
                mastodon.account_follow(id)
        if request.POST.get("ic-request"):
            sleep(
                1
            )  # This is annoying, but the next call will return Requested instead of Following in some cases
            relationship = mastodon.account_relationships(user_dict.id)[0]
            return render(
                request,
                "intercooler/follow.html",
                {
                    "user": user_dict,
                    "relationship": relationship,
                    "own_acct": request.session["active_user"],
                    "preferences": account.preferences,
                },
            )
        else:
            return redirect(user, user_dict.acct)
    else:
        return render(
            request,
            "main/follow.html",
            {
                "user": user_dict,
                "relationship": relationship,
                "confirm_page": True,
                "own_acct": request.session["active_user"],
                "preferences": account.preferences,
            },
        )


@never_cache
@br_login_required
def block(request, id):
    account, mastodon = get_usercontext(request)
    try:
        user_dict = mastodon.account(id)
        relationship = mastodon.account_relationships(user_dict.id)[0]
    except (IndexError, AttributeError, KeyError):
        raise Http404("The user could not be found.")
    if request.method == "POST":
        if not request.POST.get("cancel", None):
            if relationship.blocking:
                mastodon.account_unblock(id)
            else:
                mastodon.account_block(id)
            if request.POST.get("ic-request"):
                relationship["blocking"] = not relationship["blocking"]
                return render(
                    request,
                    "intercooler/block.html",
                    {"user": user_dict, "relationship": relationship},
                )
            else:
                return redirect(user, user_dict.acct)
    else:
        return render(
            request,
            "main/block.html",
            {
                "user": user_dict,
                "relationship": relationship,
                "confirm_page": True,
                "own_acct": request.session["active_user"],
                "preferences": account.preferences,
            },
        )


@never_cache
@br_login_required
def mute(request, id):
    account, mastodon = get_usercontext(request)
    try:
        user_dict = mastodon.account(id)
        relationship = mastodon.account_relationships(user_dict.id)[0]
    except (IndexError, AttributeError, KeyError):
        raise Http404("The user could not be found.")
    if request.method == "POST":
        if not request.POST.get("cancel", None):
            if relationship.muting:
                mastodon.account_unmute(id)
            else:
                mastodon.account_mute(id)
            if request.POST.get("ic-request"):
                relationship["muting"] = not relationship["muting"]
                return render(
                    request,
                    "intercooler/mute.html",
                    {"user": user_dict, "relationship": relationship},
                )
            else:
                return redirect(user, user_dict.acct)
    else:
        return render(
            request,
            "main/mute.html",
            {
                "user": user_dict,
                "relationship": relationship,
                "confirm_page": True,
                "own_acct": request.session["active_user"],
                "preferences": account.preferences,
            },
        )


@br_login_required
def search(request):
    account, mastodon = get_usercontext(request)
    if request.GET.get("ic-request"):
        return render(
            request,
            "intercooler/search.html",
            {
                "preferences": account.preferences,
                "own_acct": request.session["active_user"],
            },
        )
    else:
        return render(
            request,
            "main/search.html",
            {
                "preferences": account.preferences,
                "own_acct": request.session["active_user"],
            },
        )


@br_login_required
@cache_page(60 * 5)
def search_results(request):
    if request.method == "GET":
        query = request.GET.get("q", "")
    elif request.method == "POST":
        query = request.POST.get("q", "")
    else:
        query = ""
    account, mastodon = get_usercontext(request)
    results = mastodon.search(query)
    notifications = _notes_count(account, mastodon)
    return render(
        request,
        "main/search_results.html",
        {
            "results": results,
            "own_acct": request.session["active_user"],
            "notifications": notifications,
            "preferences": account.preferences,
        },
    )


@cache_page(60 * 30)
def about(request):
    version = django_settings.BRUTALDON_VERSION
    account, mastodon = get_usercontext(request)
    if account:
        preferences = account.preferences
    else:
        preferences = None
    return render(
        request,
        "about.html",
        {
            "preferences": preferences,
            "version": version,
            "own_acct": request.session.get("active_user", None),
        },
    )


@cache_page(60 * 30)
def privacy(request):
    account, mastodon = get_usercontext(request)
    if account:
        preferences = account.preferences
    else:
        preferences = None
    return render(
        request,
        "privacy.html",
        {
            "preferences": preferences,
            "own_acct": request.session.get("active_user", None),
        },
    )


@cache_page(60 * 30)
@br_login_required
def emoji_reference(request):
    account, mastodon = get_usercontext(request)
    emojos = mastodon.custom_emojis()
    notifications = _notes_count(account, mastodon)
    return render(
        request,
        "main/emoji.html",
        {
            "preferences": account.preferences,
            "emojos": sorted(emojos, key=lambda x: x["shortcode"]),
            "notifications": notifications,
            "own_acct": request.session["active_user"],
        },
    )


@br_login_required
def list_filters(request):
    account, mastodon = get_usercontext(request)
    filters = mastodon.filters()
    return render(
        request,
        "filters/list.html",
        {"account": account, "preferences": account.preferences, "filters": filters},
    )


@br_login_required
def create_filter(request):
    account, mastodon = get_usercontext(request)
    if request.method == "POST":
        form = FilterForm(request.POST)
        if form.is_valid():
            contexts = []
            if form.cleaned_data["context_home"]:
                contexts.append("home")
            if form.cleaned_data["context_public"]:
                contexts.append("public")
            if form.cleaned_data["context_notes"]:
                contexts.append("notifications")
            if form.cleaned_data["context_thread"]:
                contexts.append("thread")
            expires = form.cleaned_data["expires_in"]
            if expires == "":
                expires = None
            mastodon.filter_create(
                form.cleaned_data["phrase"],
                contexts,
                whole_word=form.cleaned_data["whole_word"],
                expires_in=expires,
            )
            return redirect(list_filters)
        else:
            return render(
                request,
                "filters/create.html",
                {"form": form, "account": account, "preferences": account.preferences},
            )
    else:
        form = FilterForm()
        return render(
            request,
            "filters/create.html",
            {"form": form, "account": account, "preferences": account.preferences},
        )


@br_login_required
def delete_filter(request, id):
    account, mastodon = get_usercontext(request)
    filter = mastodon.filter(id)

    if request.method == "POST" or request.method == "DELETE":
        if not request.POST.get("cancel", None):
            mastodon.filter_delete(filter.id)
            if request.POST.get("ic-request"):
                return HttpResponse("")
        return redirect(list_filters)
    else:
        return render(
            request,
            "filters/delete.html",
            {
                "filter": filter,
                "own_acct": request.session["active_user"],
                "confirm_page": True,
                "preferences": account.preferences,
            },
        )


@br_login_required
def edit_filter(request, id):
    account, mastodon = get_usercontext(request)
    filter = mastodon.filter(id)

    contexts = []
    if request.method == "POST":
        form = FilterForm(request.POST)
        if form.is_valid():
            if form.cleaned_data["context_home"]:
                contexts.append("home")
            if form.cleaned_data["context_public"]:
                contexts.append("public")
            if form.cleaned_data["context_notes"]:
                contexts.append("notifications")
            if form.cleaned_data["context_thread"]:
                contexts.append("thread")
            expires = form.cleaned_data["expires_in"]
            if expires == "":
                expires = None
            mastodon.filter_update(
                id,
                form.cleaned_data["phrase"],
                contexts,
                whole_word=form.cleaned_data["whole_word"],
                expires_in=expires,
            )
            return redirect(list_filters)
        else:
            return render(
                request,
                "filters/edit.html",
                {
                    "form": form,
                    "account": account,
                    "filter": filter,
                    "preferences": account.preferences,
                },
            )
    else:
        contexts = []
        form = FilterForm(
            {
                "phrase": filter.phrase,
                "context_home": "home" in filter.context,
                "context_public": "public" in filter.context,
                "context_notes": "notifications" in filter.context,
                "context_thread": "thread" in filter.context,
                "whole_word": filter.whole_word,
            }
        )
        return render(
            request,
            "filters/edit.html",
            {
                "form": form,
                "account": account,
                "filter": filter,
                "preferences": account.preferences,
            },
        )


@br_login_required
def follow_requests(request, id=None):
    account, mastodon = get_usercontext(request)
    if request.method == "GET":
        reqs = mastodon.follow_requests()
        return render(
            request,
            "requests/list.html",
            {"account": account, "preferences": account.preferences, "requests": reqs},
        )
    elif id is None:
        return redirect(follow_requests)
    else:
        if request.POST.get("accept", None):
            mastodon.follow_request_authorize(id)
        elif request.POST.get("reject", None):
            mastodon.follow_request_reject(id)
        return redirect(follow_requests)


@br_login_required
def accounts(request, id=None):
    active_account, mastodon = get_usercontext(request)
    if request.method == "GET":
        accounts = [x for x in request.session.get("accounts_dict").values()]
        return render(
            request,
            "accounts/list.html",
            {
                "active_account": active_account,
                "own_acct": request.session["active_user"],
                "accounts": accounts,
                "preferences": active_account.preferences,
            },
        )
    if request.method == "POST":
        if request.POST.get("activate"):
            to_account = Account.objects.get(id=id).username
            if switch_accounts(request, to_account):
                return redirect(home)
            else:
                return redirect("accounts")
        elif request.POST.get("forget"):
            account = Account.objects.get(id=id).username
            return forget_account(request, account)
        else:
            accounts = [x for x in request.session.get("accounts_dict").values()]
            return render(
                request,
                "accounts/list.html",
                {
                    "active_account": active_account,
                    "own_acct": request.session["active_user"],
                    "accounts": accounts,
                    "preferences": active_account.preferences,
                },
            )
