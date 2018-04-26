from django.http import HttpResponse
from django.shortcuts import render, redirect
from brutaldon.forms import LoginForm, SettingsForm
from brutaldon.models import Client, Account
from mastodon import Mastodon
from urllib import parse

class NotLoggedInException(Exception):
    pass

def get_mastodon(request):
    if not (request.session.has_key('instance') and
            request.session.has_key('username')):
        raise NotLoggedInException()

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
        ratelimit_method="pace")
    return mastodon

def fullbrutalism_p(request):
    if request.session.has_key('fullbrutalism'):
        fullbrutalism = request.session['fullbrutalism']
    else:
        fullbrutalism = False
    return fullbrutalism

def timeline(request, timeline='home', timeline_name='Home'):
    try:
        mastodon = get_mastodon(request)
    except NotLoggedInException:
        return redirect(login)
    data = mastodon.timeline(timeline)
    return render(request, 'main/timeline.html',
                  {'toots': data, 'timeline': timeline_name,
                   'fullbrutalism': fullbrutalism_p(request)})

def home(request):
    return timeline(request, 'home', 'Home')

def local(request):
    return timeline(request, 'local', 'Local')

def fed(request):
    return timeline(request, 'public', 'Federated')

def login(request):
    if request.method == "GET":
        form = LoginForm()
        return render(request, 'setup/login.html', {'form': form})
    elif request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            api_base_url = form.cleaned_data['instance']
            # Fixme, make sure this is url
            tmp_base = parse.urlparse(api_base_url.lower())
            if tmp_base.netloc == '':
                api_base_url = parse.urlunparse(('https', tmp_base.path,
                                                 '','','',''))
            else:
                api_base_url = api_base_url.lower()

            request.session['instance'] = api_base_url
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                client = Client.objects.get(api_base_id=api_base_url)
            except (Client.DoesNotExist, Client.MultipleObjectsReturned):
                (client_id, client_secret) = Mastodon.create_app('brutaldon',
                                                             api_base_url=api_base_url)
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
                account = Account.objects.get(username=username, client_id=client.id)
            except (Account.DoesNotExist, Account.MultipleObjectsReturned):
                account = Account(
                    username = username,
                    access_token = access_token,
                    client = client)
                access_token = mastodon.log_in(username,
                                               password)
                account.save()
            request.session['username'] = username

            return redirect(home)
        else:
            return render(request, 'setup/login.html', {'form': form})

def logout(request):
    request.session.flush()
    return redirect(home)

def error(request):
    return render(request, 'error.html', { 'error': "Not logged in yet."})

def note(request):
    mastodon = get_mastodon(request)
    notes = mastodon.notifications()
    return render(request, 'main/notifications.html',
                  {'notes': notes,'timeline': 'Notifications',
                   'fullbrutalism': fullbrutalism_p(request)})


def settings(request):
    if request.method == 'POST':
        form = SettingsForm(request.POST)
        if form.is_valid():
            request.session['fullbrutalism'] = form.cleaned_data['fullbrutalism']
            return redirect(home)
        else:
            return render(request, 'setup/settings.html',
                          {'form' : form, 'fullbrutalism': fullbrutalism_p(request)})
    else:
        form = SettingsForm(request.session)
        return render(request, 'setup/settings.html',
                      { 'form': form, 'fullbrutalism': fullbrutalism_p(request)})

