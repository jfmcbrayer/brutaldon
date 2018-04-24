from django.http import HttpResponse
from django.shortcuts import render, redirect
from brutaldon.forms import LoginForm
from brutaldon.models import Client, Account
from mastodon import Mastodon
import datetime
from urllib import parse

def home(request):
    now = datetime.datetime.now()
    if not (request.session.has_key('instance') and
            request.session.has_key('username')):
        return redirect(login)

    try:
        client = Client.objects.get(api_base_id=request.session['instance'])
        user = Account.objects.get(username=request.session['username'])
    except (Client.DoesNotExist, Client.MultipleObjectsReturned,
            Account.DoesNotExist, Account.MultipleObjectsReturned):
        return redirect(login)

    mastodon = Mastodon(
        client_id = client.client_id,
        client_secret = client.client_secret,
        access_token = user.access_token,
        api_base_url = client.api_base_id,
        ratelimit_method="pace")
    data = mastodon.timeline()
    return render(request, 'main/timeline.html',
                  {'toots': data, 'timeline': 'Home' })


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
            access_token = mastodon.log_in(username,
                                           password)

            try:
                account = Account.objects.get(username=username, client_id=client.id)
                account.access_token = access_token
            except (Account.DoesNotExist, Account.MultipleObjectsReturned):
                account = Account(
                    username = username,
                    access_token = access_token,
                    client = client)
            account.save()
            request.session['username'] = username

            return redirect(home)
        else:
            return render(request, 'setup/login.html', {'form': form})

def logout(request):
    return redirect(error)

def error(request):
    return render(request, 'error.html', { 'error': "Not logged in yet."})

def note(request):
    return render(request, 'main/timeline.html', {'timeline': 'Notifications'})

def local(request):
    return render(request, 'main/timeline.html', {'timeline': 'Local'})

def fed(request):
    return render(request, 'main/timeline.html', {'timeline': 'Federated'})

