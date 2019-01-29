from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.conf import settings as django_settings
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache, cache_page
from django.urls import reverse
from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.utils.translation import gettext as _
from brutaldon.forms import LoginForm, OAuthLoginForm, PreferencesForm, PostForm
from brutaldon.models import Client, Account, Preference, Theme
from mastodon import Mastodon, AttribAccessDict, MastodonError, MastodonAPIError
from urllib import parse
from pdb import set_trace
from inscriptis import get_text
from time import sleep
import re

class NotLoggedInException(Exception):
    pass

def get_usercontext(request):
    if is_logged_in(request):
        try:
            client = Client.objects.get(api_base_id=request.session['instance'])
            user = Account.objects.get(username=request.session['username'])
        except (Client.DoesNotExist, Client.MultipleObjectsReturned,
                Account.DoesNotExist, Account.MultipleObjectsReturned):
            raise NotLoggedInException()
        mastodon = Mastodon(
            client_id = client.client_id,
            client_secret = client.client_secret,
            access_token = user.access_token,
            api_base_url = client.api_base_id,
            ratelimit_method="throw")
        return user, mastodon
    else:
        return None, None

def is_logged_in(request):
    return request.session.has_key('user')

def _notes_count(account, mastodon):
    if not mastodon:
        return ""
    notes = mastodon.notifications(limit=40)
    if account.preferences.filter_notifications:
        notes = [ note for note in notes if note.type == 'mention' or note.type == 'follow']
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

def notes_count(request):
    account, mastodon = get_usercontext(request)
    count = _notes_count(account, mastodon)
    return render(request, 'intercooler/notes.html',
                  {'notifications': count,
                   'preferences': account.preferences })

def user_search(request):
    check = request.POST.get("status", "").split()
    if len(check):
        check = check[-1]
        if len(check) > 1 and check.startswith('@'):
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
    return render(request, 'intercooler/users.html',
                  {'users': "\n".join([ user.acct for user in results.accounts ]),
                   'preferences': account.preferences })

def timeline(request, timeline='home', timeline_name='Home', max_id=None, since_id=None):
    account, mastodon = get_usercontext(request)
    data = mastodon.timeline(timeline, limit=40, max_id=max_id, since_id=since_id)
    form = PostForm(initial={'visibility': request.session['user'].source.privacy})
    try:
        prev = data[0]._pagination_prev
        if len(mastodon.timeline(since_id=prev['since_id'])) == 0:
            prev = None
        else:
            prev['since_id'] = data[0].id
    except (IndexError, AttributeError):
        prev = None
    try:
        next = data[-1]._pagination_next
        next['max_id'] = data[-1].id
    except (IndexError, AttributeError):
        next = None

    notifications = _notes_count(account, mastodon)

    # This filtering has to be done *after* getting next/prev links
    if account.preferences.filter_replies:
        data = [x for x in data if not x.in_reply_to_id]
    if account.preferences.filter_boosts:
        data = [x for x in data if not x.reblog]
    return render(request, 'main/%s_timeline.html' % timeline,
                  {'toots': data, 'form': form, 'timeline': timeline,
                   'timeline_name': timeline_name,
                   'own_acct': request.session['user'],
                   'preferences': account.preferences,
                   'notifications': notifications,
                  'prev': prev, 'next': next})

@br_login_required
def home(request, next=None, prev=None):
    return timeline(request, 'home', 'Home', max_id=next, since_id=prev)

@br_login_required
def local(request, next=None, prev=None):
    return timeline(request, 'local', 'Local', max_id=next, since_id=prev)

@br_login_required
def fed(request, next=None, prev=None):
    return timeline(request, 'public', 'Federated', max_id=next, since_id=prev)

@br_login_required
def tag(request, tag):
    try:
        account, mastodon = get_usercontext(request)
    except NotLoggedInException:
        return redirect(login)
    data = mastodon.timeline_hashtag(tag)
    notifications = _notes_count(account, mastodon)
    return render(request, 'main/timeline.html',
                  {'toots': data, 'timeline_name': '#'+tag,
                   'own_acct': request.session['user'],
                   'notifications': notifications,
                   'preferences': account.preferences})

@never_cache
def login(request):
    # User posts instance name in form.
    # POST page redirects user to instance, where they log in.
    # Instance redirects user to oauth_after_login view.
    # oauth_after_login view saves credential in session, then redirects to home.
    if request.method == "GET":
        form = OAuthLoginForm()
        return render(request, 'setup/login-oauth.html', {'form': form})
    elif request.method == "POST":
        form = OAuthLoginForm(request.POST)
        redirect_uris = request.build_absolute_uri(reverse('oauth_callback'))
        if form.is_valid():
            api_base_url = form.cleaned_data['instance']
            tmp_base = parse.urlparse(api_base_url.lower())
            if tmp_base.netloc == '':
                api_base_url = parse.urlunparse(('https', tmp_base.path,
                                                 '','','',''))
                request.session['instance_hostname'] = tmp_base.path
            else:
                api_base_url = api_base_url.lower()
                request.session['instance_hostname'] = tmp_base.netloc

            request.session['instance'] = api_base_url
            try:
                client = Client.objects.get(api_base_id=api_base_url)
            except (Client.DoesNotExist, Client.MultipleObjectsReturned):
                (client_id, client_secret) = Mastodon.create_app('brutaldon',
                                    api_base_url=api_base_url,
                                    redirect_uris=redirect_uris,
                                    scopes=['read', 'write', 'follow'])
                client = Client(
                    api_base_id = api_base_url,
                    client_id=client_id,
                    client_secret = client_secret)
                client.save()

            request.session['client_id'] = client.client_id
            request.session['client_secret'] = client.client_secret

            mastodon = Mastodon(
                client_id = client.client_id,
                client_secret = client.client_secret,
                api_base_url = api_base_url)
            return redirect(mastodon.auth_request_url(redirect_uris=redirect_uris,
                                                      scopes=['read', 'write', 'follow']))
        else:
            return render(request, 'setup/login.html', {'form': form})

    else:
        return redirect(login)

@never_cache
def oauth_callback(request):
    code = request.GET.get('code', '')
    mastodon = Mastodon(client_id=request.session['client_id'],
                        client_secret=request.session['client_secret'],
                        api_base_url=request.session['instance'])
    redirect_uri = request.build_absolute_uri(reverse('oauth_callback'))
    access_token = mastodon.log_in(code=code,
                                   redirect_uri=redirect_uri,
                                   scopes=['read', 'write', 'follow'])
    request.session['access_token'] = access_token
    user = mastodon.account_verify_credentials()
    try:
        account = Account.objects.get(username=user.username + '@' +
                                      request.session['instance_hostname'])
        account.access_token = access_token
        if not account.preferences:
            preferences = Preference(theme = Theme.objects.get(id=1))
            preferences.save()
            account.preferences = preferences
        else:
            request.session['timezone'] = account.preferences.timezone
        account.save()
    except (Account.DoesNotExist, Account.MultipleObjectsReturned):
        preferences = Preference(theme = Theme.objects.get(id=1))
        preferences.save()
        account = Account(username=user.username + '@' + request.session['instance_hostname'],
                          access_token = access_token,
                          client = Client.objects.get(api_base_id=request.session['instance']),
                          preferences = preferences)
        account.save()
    request.session['user'] = user
    request.session['username'] = user.username + '@' + request.session['instance_hostname']
    return redirect(home)


@never_cache
def old_login(request):
    if request.method == "GET":
        form = LoginForm()
        return render(request, 'setup/login.html', {'form': form})
    elif request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            api_base_url = form.cleaned_data['instance']
            tmp_base = parse.urlparse(api_base_url.lower())
            if tmp_base.netloc == '':
                api_base_url = parse.urlunparse(('https', tmp_base.path,
                                                 '','','',''))
                request.session['instance_hostname'] = tmp_base.path
            else:
                api_base_url = api_base_url.lower()
                request.session['instance_hostname'] = tmp_base.netloc

            request.session['instance'] = api_base_url
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                client = Client.objects.get(api_base_id=api_base_url)
            except (Client.DoesNotExist, Client.MultipleObjectsReturned):
                (client_id, client_secret) = Mastodon.create_app('brutaldon',
                                                     api_base_url=api_base_url,
                                                     scopes=['read', 'write', 'follow'])
                client = Client(
                    api_base_id = api_base_url,
                    client_id=client_id,
                    client_secret = client_secret)
                client.save()

            mastodon = Mastodon(
                client_id = client.client_id,
                client_secret = client.client_secret,
                api_base_url = api_base_url)

            try:
                account = Account.objects.get(email=email, client_id=client.id)
            except (Account.DoesNotExist, Account.MultipleObjectsReturned):
                preferences = Preference(theme = Theme.objects.get(id=1))
                preferences.save()
                account = Account(
                    email = email,
                    access_token = "",
                    client = client,
                    preferences = preferences)
            try:
                access_token = mastodon.log_in(email,
                                               password,
                                               scopes=['read', 'write', 'follow'])
                account.access_token = access_token
                user = mastodon.account_verify_credentials()
                request.session['user'] = user
                request.session['username'] = user.username + '@' + request.session['instance_hostname']
                account.username = request.session['username']
                request.session['timezone'] = account.preferences.timezone;
                account.save()
                return redirect(home)

            except Exception as ex:
                form.add_error('', ex)
                return render(request, 'setup/login.html', {'form': form})
        else:
            return render(request, 'setup/login.html', {'form': form})

@never_cache
def logout(request):
    request.session.flush()
    return redirect(about)

def error(request):
    return render(request, 'error.html', { 'error': _("Not logged in yet.")})

@br_login_required
def note(request, next=None, prev=None):
    try:
        account, mastodon = get_usercontext(request)
    except NotLoggedInException:
        return redirect(about)
    last_seen = mastodon.notifications(limit=1)[0]
    account.note_seen = last_seen.id
    account.save()

    notes = mastodon.notifications(limit=40, max_id=next, since_id=prev)
    if account.preferences.filter_notifications:
        notes = [ note for note in notes if note.type == 'mention' or note.type == 'follow']
    try:
        prev = notes[0]._pagination_prev
        if len(mastodon.notifications(since_id=prev['since_id'])) == 0:
            prev = None
    except (IndexError, AttributeError):
        prev = None
    try:
        next = notes[-1]._pagination_next
    except (IndexError, AttributeError):
        next = None
    return render(request, 'main/notifications.html',
                  {'notes': notes,'timeline': 'Notifications',
                   'timeline_name': 'Notifications',
                   'own_acct': request.session['user'],
                   'preferences': account.preferences,
                  'prev': prev, 'next': next})

@br_login_required
def thread(request, id):
    account, mastodon = get_usercontext(request)
    context = mastodon.status_context(id)
    toot = mastodon.status(id)
    notifications = _notes_count(account, mastodon)
    return render(request, 'main/thread.html',
                  {'context': context, 'toot': toot,
                   'own_acct': request.session['user'],
                   'notifications': notifications,
                   'preferences': account.preferences})

@br_login_required
def user(request, username, prev=None, next=None):
    try:
        account, mastodon = get_usercontext(request)
    except NotLoggedInException:
        return redirect(about)
    try:
        user_dict = [dict for dict in mastodon.account_search(username)
                     if ((dict.acct == username) or
                         (dict.acct == username.split('@')[0] and
                          username.split('@')[1] == account.username.split('@')[1]))][0]
    except (IndexError, AttributeError):
        raise Http404(_("The user %s could not be found.") % username)
    data = mastodon.account_statuses(user_dict.id, max_id=next, since_id=prev)
    relationship = mastodon.account_relationships(user_dict.id)[0]
    notifications = _notes_count(account, mastodon)
    try:
        prev = data[0]._pagination_prev
        if len(mastodon.account_statuses(user_dict.id,
                                         since_id=prev['since_id'])) == 0:
            prev = None
    except (IndexError, AttributeError):
        prev = None
    try:
        next = data[-1]._pagination_next
    except (IndexError, AttributeError):
        next = None
    return render(request, 'main/user.html',
                  {'toots': data, 'user': user_dict,
                   'relationship': relationship,
                   'own_acct': request.session['user'],
                   'preferences': account.preferences,
                   'notifications': notifications,
                  'prev': prev, 'next': next})


@never_cache
@br_login_required
def settings(request):
    account = Account.objects.get(username=request.session['username'])
    if request.method == 'POST':
        form = PreferencesForm(request.POST)
        if form.is_valid():
            account.preferences.theme = form.cleaned_data['theme']
            account.preferences.filter_replies = form.cleaned_data['filter_replies']
            account.preferences.filter_boosts = form.cleaned_data['filter_boosts']
            account.preferences.timezone = form.cleaned_data['timezone']
            account.preferences.no_javascript = form.cleaned_data['no_javascript']
            account.preferences.notifications = form.cleaned_data['notifications']
            account.preferences.click_to_load = form.cleaned_data['click_to_load']
            account.preferences.lightbox = form.cleaned_data['lightbox']
            account.preferences.filter_notifications = form.cleaned_data['filter_notifications']
            request.session['timezone'] = account.preferences.timezone
            account.preferences.save()
            account.save()
            return redirect(home)
        else:
            return render(request, 'setup/settings.html',
                          {'form' : form, 'account': account})
    else:
        request.session['timezone'] = account.preferences.timezone
        form = PreferencesForm(instance=account.preferences)
        return render(request, 'setup/settings.html',
                      { 'form': form,
                        'account': account,
                        'preferences': account.preferences})

@never_cache
@br_login_required
def toot(request, mention=None):
    account, mastodon = get_usercontext(request)
    if request.method == 'GET':
        if mention:
            if not mention.startswith('@'):
                mention = '@'+mention
            form = PostForm(initial={'visibility': request.session['user'].source.privacy,
                                     'status': mention + ' ' })
        else:
            form = PostForm(initial={'visibility': request.session['user'].source.privacy})
        if request.GET.get('ic-request'):
            return render(request, 'intercooler/post.html',
                          {'form': form,
                           'own_acct': request.session['user'],
                           'preferences': account.preferences})
        else:
            return render(request, 'main/post.html',
                          {'form': form,
                           'own_acct': request.session['user'],
                           'preferences': account.preferences})
    elif request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            # create media objects
            media_objects = []
            for index in range(1,5):
                if 'media_file_'+str(index) in request.FILES:
                    media_objects.append(
                        mastodon.media_post(request.FILES['media_file_'+str(index)]
                                            .temporary_file_path(),
                                            description=request.POST.get('media_text_'
                                                                         +str(index),
                                                                         None)))
            if form.cleaned_data['visibility'] == '':
                form.cleaned_data['visibility'] = request.session['user'].source.privacy
            try:
                try:
                    mastodon.status_post(status=form.cleaned_data['status'],
                                         visibility=form.cleaned_data['visibility'],
                                         spoiler_text=form.cleaned_data['spoiler_text'],
                                         media_ids=media_objects,
                                         content_type='text/markdown')
                except TypeError:
                    mastodon.status_post(status=form.cleaned_data['status'],
                                         visibility=form.cleaned_data['visibility'],
                                         spoiler_text=form.cleaned_data['spoiler_text'],
                                         media_ids=media_objects)
            except MastodonAPIError as error:
                form.add_error("", "%s (%s used)" % (error.args[-1],
                                                     len(form.cleaned_data['status'])
                                                     + len(form.cleaned_data['spoiler_text'])))
                return render(request, 'main/post.html',
                              {'form': form,
                               'own_acct': request.session['user'],
                               'preferences': account.preferences})
            return redirect(home)
        else:
            return render(request, 'main/post.html',
                          {'form': form,
                           'own_acct': request.session['user'],
                           'preferences': account.preferences})
    else:
        return redirect(toot)

@br_login_required
def redraft(request, id):
    if request.method == 'GET':
        account, mastodon = get_usercontext(request)
        toot = mastodon.status(id)
        toot_content = get_text(toot.content)
        toot_content = re.sub("(^\n)|(\n$)", '', re.sub("\n\n", "\n", toot_content))
        form = PostForm({'status': toot_content,
                         'visibility': toot.visibility,
                         'spoiler_text': toot.spoiler_text,
                         'media_text_1': safe_get_attachment(toot, 0).description,
                         'media_text_2': safe_get_attachment(toot, 1).description,
                         'media_text_3': safe_get_attachment(toot, 2).description,
                         'media_text_4': safe_get_attachment(toot, 3).description,
        })
        return render(request, 'main/redraft.html',
                      {'toot': toot, 'form': form, 'redraft':True,
                       'own_acct': request.session['user'],
                       'preferences': account.preferences})
    elif request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        account, mastodon = get_usercontext(request)
        toot = mastodon.status(id)
        if form.is_valid():
            media_objects = []
            for index in range(1,5):
                if 'media_file_'+str(index) in request.FILES:
                    media_objects.append(
                        mastodon.media_post(request.FILES['media_file_'+str(index)]
                                            .temporary_file_path(),
                                            description=request.POST.get('media_text_'
                                                                         +str(index),
                                                                         None)))
            if form.cleaned_data['visibility'] == '':
                form.cleaned_data['visibility'] = request.session['user'].source.privacy
            try:
                try:
                    mastodon.status_post(status=form.cleaned_data['status'],
                                         visibility=form.cleaned_data['visibility'],
                                         spoiler_text=form.cleaned_data['spoiler_text'],
                                         media_ids=media_objects,
                                         in_reply_to_id=toot.in_reply_to_id,
                                         content_type='text/markdown')
                except TypeError:
                    mastodon.status_post(status=form.cleaned_data['status'],
                                         visibility=form.cleaned_data['visibility'],
                                         spoiler_text=form.cleaned_data['spoiler_text'],
                                         media_ids=media_objects,
                                         in_reply_to_id=toot.in_reply_to_id)
                mastodon.status_delete(id)
            except MastodonAPIError as error:
                form.add_error("", "%s (%s used)" % (error.args[-1],
                                                     len(form.cleaned_data['status'])
                                                     + len(form.cleaned_data['spoiler_text'])))
                return render(request, 'main/redraft.html',
                              {'toot': toot, 'form': form, 'redraft': True,
                               'own_acct': request.session['user'],
                               'preferences': account.preferences})
            return redirect(home)
        else:
            return render(request, 'main/redraft.html',
                          {'toot': toot, 'form': form, 'redraft': True,
                           'own_acct': request.session['user'],
                           'preferences': account.preferences})
    else:
        return redirect(redraft, id)

def safe_get_attachment(toot, index):
    """Get an attachment from a toot, without crashing if it isn't there."""
    try:
        return toot.media_attachments[index]
    except IndexError:
        adict = AttribAccessDict()
        adict.id, adict.type, adict.description = "", "unknown", ""
        adict.url, adict.remote_url, adict.preview_url = '', '', ''
        adict.text_url = ''
        return adict


@br_login_required
def reply(request, id):
    if request.method == 'GET':
        account, mastodon = get_usercontext(request)
        toot = mastodon.status(id)
        context = mastodon.status_context(id)
        notifications = _notes_count(account, mastodon)
        if toot.account.acct != request.session['user'].acct:
            initial_text = '@' + toot.account.acct + " "
        else:
            initial_text = ""
        for mention in [x for x in toot.mentions
                        if x.acct != request.session['user'].acct and
                        x.acct != toot.account.acct]:
            initial_text +=('@' + mention.acct + " ")
        form = PostForm(initial={'status': initial_text,
                                 'visibility': toot.visibility,
                                 'spoiler_text': toot.spoiler_text})
        return render(request, 'main/reply.html',
                      {'context': context, 'toot': toot, 'form': form, 'reply':True,
                       'own_acct': request.session['user'],
                       'notifications': notifications,
                       'preferences': account.preferences})
    elif request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        account, mastodon = get_usercontext(request)
        toot = mastodon.status(id)
        context = mastodon.status_context(id)
        notifications = _notes_count(account, mastodon)
        if form.is_valid():
            # create media objects
            media_objects = []
            for index in range(1,5):
                if 'media_file_'+str(index) in request.FILES:
                    media_objects.append(
                        mastodon.media_post(request.FILES['media_file_'+str(index)]
                                            .temporary_file_path(),
                                            description=request.POST.get('media_text_'
                                                                         +str(index),
                                                                         None)))
            try:
                try:
                    mastodon.status_post(status=form.cleaned_data['status'],
                                         visibility=form.cleaned_data['visibility'],
                                         spoiler_text=form.cleaned_data['spoiler_text'],
                                         media_ids=media_objects,
                                         in_reply_to_id=id,
                                         content_type="text/markdown")
                except TypeError:
                    mastodon.status_post(status=form.cleaned_data['status'],
                                         visibility=form.cleaned_data['visibility'],
                                         spoiler_text=form.cleaned_data['spoiler_text'],
                                         media_ids=media_objects,
                                         in_reply_to_id=id)
            except MastodonAPIError as error:
                form.add_error("", "%s (%s used)" % (error.args[-1],
                                                     len(form.cleaned_data['status'])
                                                     + len(form.cleaned_data['spoiler_text'])))
                return render(request, 'main/reply.html',
                              {'context': context, 'toot': toot, 'form': form, 'reply': True,
                               'own_acct': request.session['user'],
                               'notifications': notifications,
                               'preferences': account.preferences})
            return redirect(thread, id)
        else:
            return render(request, 'main/reply.html',
                          {'context': context, 'toot': toot, 'form': form, 'reply': True,
                           'own_acct': request.session['user'],
                           'preferences': account.preferences})
    else:
        return redirect(reply, id)

@never_cache
@br_login_required
def fav(request, id):
    account, mastodon = get_usercontext(request)
    toot = mastodon.status(id)
    if request.method == 'POST':
        if not request.POST.get('cancel', None):
            if toot.favourited:
                mastodon.status_unfavourite(id)
            else:
                mastodon.status_favourite(id)
        if request.POST.get('ic-request'):
            toot['favourited'] = not toot['favourited']
            return render(request, 'intercooler/fav.html',
                          {"toot": toot,
                           'own_acct': request.session['user'],
                           "preferences": account.preferences})
        else:
            return HttpResponseRedirect(reverse('thread', args=[id]) + "#toot-"+str(id))
    else:
        return render(request, 'main/fav.html',
                      {"toot": toot,
                       'own_acct': request.session['user'],
                       "confirm_page": True,
                       'preferences': account.preferences})

@never_cache
@br_login_required
def boost(request, id):
    account, mastodon = get_usercontext(request)
    toot = mastodon.status(id)
    if request.method == 'POST':
        if not request.POST.get('cancel', None):
            if toot.reblogged:
                mastodon.status_unreblog(id)
            else:
                mastodon.status_reblog(id)
        if request.POST.get('ic-request'):
            toot['reblogged'] = not toot['reblogged']
            return render(request, 'intercooler/boost.html',
                          {"toot": toot,
                           'own_acct': request.session['user'],
                           "preferences": account.preferences})
        else:
            return HttpResponseRedirect(reverse('thread', args=[id]) + "#toot-"+str(id))
    else:
        return render(request, 'main/boost.html',
                      {"toot": toot,
                       'own_acct': request.session['user'],
                       'confirm_page': True,
                       "preferences": account.preferences})

@never_cache
@br_login_required
def delete(request, id):
    account, mastodon = get_usercontext(request)
    toot = mastodon.status(id)
    if request.method == 'POST' or request.method == 'DELETE':
        if toot.account.acct != request.session['user'].acct:
            return redirect('home')
        if not request.POST.get('cancel', None):
            mastodon.status_delete(id)
            if request.POST.get('ic-request') or request.DELETE.get('ic-request'):
                return HttpResponse("")
        return redirect(home)
    else:
        return render(request, 'main/delete.html',
                      {"toot": toot,
                       'own_acct': request.session['user'],
                       'confirm_page': True,
                       "preferences": account.preferences})

@never_cache
@br_login_required
def follow(request, id):
    account, mastodon = get_usercontext(request)
    try:
        user_dict = mastodon.account(id)
        relationship = mastodon.account_relationships(user_dict.id)[0]
    except (IndexError, AttributeError):
        raise Http404("The user could not be found.")
    if request.method == 'POST':
        if not request.POST.get('cancel', None):
            if relationship.requested or relationship.following:
                mastodon.account_unfollow(id)
            else:
                mastodon.account_follow(id)
        if request.POST.get('ic-request'):
            sleep(1) # This is annoying, but the next call will return Requested instead of Following in some cases
            relationship = mastodon.account_relationships(user_dict.id)[0]
            return render(request, 'intercooler/follow.html',
                      {"user": user_dict, "relationship": relationship,
                       'own_acct':  request.session['user'],
                       'preferences': account.preferences})
        else:
            return redirect(user, user_dict.acct)
    else:
        return render(request, 'main/follow.html',
                      {"user": user_dict, "relationship": relationship,
                       "confirm_page": True,
                       'own_acct':  request.session['user'],
                       'preferences': account.preferences})

@never_cache
@br_login_required
def block(request, id):
    account, mastodon = get_usercontext(request)
    try:
        user_dict = mastodon.account(id)
        relationship = mastodon.account_relationships(user_dict.id)[0]
    except (IndexError, AttributeError):
        raise Http404("The user could not be found.")
    if request.method == 'POST':
        if not request.POST.get('cancel', None):
            if relationship.blocking:
                mastodon.account_unblock(id)
            else:
                mastodon.account_block(id)
            if request.POST.get('ic-request'):
                relationship['blocking'] = not relationship['blocking']
                return render(request, 'intercooler/block.html',
                              {"user": user_dict,
                               "relationship": relationship,
                              })
            else:
                return redirect(user, user_dict.acct)
    else:
        return render(request, 'main/block.html',
                      {"user": user_dict, "relationship": relationship,
                       "confirm_page": True,
                       'own_acct': request.session['user'],
                       'preferences': account.preferences})

@never_cache
@br_login_required
def mute(request, id):
    account, mastodon = get_usercontext(request)
    try:
        user_dict = mastodon.account(id)
        relationship = mastodon.account_relationships(user_dict.id)[0]
    except (IndexError, AttributeError):
        raise Http404("The user could not be found.")
    if request.method == 'POST':
        if not request.POST.get('cancel', None):
            if relationship.muting:
                mastodon.account_unmute(id)
            else:
                mastodon.account_mute(id)
            if request.POST.get('ic-request'):
                relationship['muting'] = not relationship['muting']
                return render(request, 'intercooler/mute.html',
                      {"user": user_dict,
                       "relationship": relationship,
                      })
            else:
                return redirect(user, user_dict.acct)
    else:
        return render(request, 'main/mute.html',
                      {"user": user_dict, "relationship": relationship,
                       "confirm_page": True,
                       'own_acct':  request.session['user'],
                       'preferences': account.preferences})

@br_login_required
def search(request):
    account, mastodon = get_usercontext(request)
    if request.GET.get('ic-request'):
        return render(request, 'intercooler/search.html',
                      {"preferences": account.preferences,
                       'own_acct':  request.session['user'],
                      })
    else:
        return render(request, 'main/search.html',
                      {"preferences": account.preferences,
                       'own_acct':  request.session['user'],
                      })

@br_login_required
def search_results(request):
    if request.method == 'GET':
        query = request.GET.get('q', '')
    elif request.method == 'POST':
        query = request.POST.get('q', '')
    else:
        query = ''
    account, mastodon = get_usercontext(request)
    results = mastodon.search(query)
    notifications = _notes_count(account, mastodon)
    return render(request, 'main/search_results.html',
                  {"results": results,
                   'own_acct': request.session['user'],
                   'notifications': notifications,
                   "preferences": account.preferences})

def about(request):
    version = django_settings.BRUTALDON_VERSION
    account, mastodon = get_usercontext(request)
    if account:
        preferences = account.preferences
    else:
        preferences = None
    return render(request, 'about.html',
                      {"preferences": preferences,
                       "version": version,
                       'own_acct': request.session.get('user', None),
                      })
def privacy(request):
    account, mastodon = get_usercontext(request)
    if account:
        preferences = account.preferences
    else:
        preferences = None
    return render(request, 'privacy.html',
                      {"preferences": preferences,
                       'own_acct' : request.session.get('user', None)})

@cache_page(60 * 30)
@br_login_required
def emoji_reference(request):
    account, mastodon = get_usercontext(request)
    emojos = mastodon.custom_emojis()
    notifications = _notes_count(account, mastodon)
    return render(request, 'main/emoji.html',
                      {"preferences": account.preferences,
                       "emojos": sorted(emojos, key=lambda x: x['shortcode']),
                       "notifications": notifications,
                       'own_acct' : request.session['user']})
