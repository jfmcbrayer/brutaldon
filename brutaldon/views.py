from django.http import HttpResponse
from django.shortcuts import render, redirect
from brutaldon.forms import LoginForm
from brutaldon.models import Client, Account
from mastodon import Mastodon
import datetime

def home(request):
    now = datetime.datetime.now()
    try:
        client = Client.objects.all()[0]
        user = Account.objects.all()[0]
    except:
        return redirect(login)

    mastodon = Mastodon(
        client_id = client.client_id,
        client_secret = client.client_secret,
        access_token = user.access_token,
        api_base_url = client.api_base_id,
        ratelimit_method="pace")
    data = mastodon.timeline()
    return render(request, 'main/timeline.html', {'toots': data })


def login(request):
    if request.method == "GET":
        form = LoginForm()
        return render(request, 'setup/login.html', {'form': form})
    elif request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            api_base_url = form.cleaned_data['instance'] # Fixme, make sure this is url
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            (client_id, client_secret) = Mastodon.create_app('brutaldon',
                                                             api_base_url=api_base_url)
            client = Client(
                api_base_id = api_base_url,
                client_id=client_id,
                client_secret = client_secret)
            client.save()

            mastodon = Mastodon(
                client_id = client_id,
                client_secret = client_secret,
                api_base_url = api_base_url)
            access_token = mastodon.log_in(username,
                                           password)
            account = Account(
                username = username,
                access_token = access_token)
            account.save()

            return redirect(home)
        else:
            return redirect(error)

def error(request):
    return render('error.html', { 'error': "Not logged in yet."})
