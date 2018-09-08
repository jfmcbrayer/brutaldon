"""brutaldon URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from brutaldon import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('about', views.about, name='about'),
    path('privacy', views.privacy, name='privacy'),
    path('home/next/<int:next>', views.home, name='home_next'),
    path('home/prev/<int:prev>', views.home, name='home_prev'),
    path('home', views.home, name='home'),
    path('login', views.login, name="login"),
    path('oldlogin', views.old_login, name="oldlogin"),
    path('logout', views.logout, name='logout'),
    path('oauth_callback', views.oauth_callback, name="oauth_callback"),
    path('error', views.error, name='error'),
    path('local', views.local, name='local'),
    path('local/next/<int:next>', views.local, name='local_next'),
    path('local/prev/<int:prev>', views.local, name='local_prev'),
    path('fed', views.fed, name='fed'),
    path('fed/next/<int:next>', views.fed, name='fed_next'),
    path('fed/prev/<int:prev>', views.fed, name='fed_prev'),
    path('note', views.note, name='note'),
    path('note/next<int:next>', views.note, name='note_next'),
    path('note/prev/<int:prev>', views.note, name='note_prev'),
    path('notes_count', views.notes_count, name='notes_count'),
    path('settings', views.settings, name='settings'),
    path('thread/<int:id>', views.thread, name='thread'),
    path('tags/<tag>', views.tag, name='tag'),
    path('user/<username>', views.user, name='user'),
    path('user/<username>/next/<int:next>', views.user, name='user_next'),
    path('user/<username>/prev/<int:prev>', views.user, name='user_prev'),
    path('toot/<mention>', views.toot, name='toot'),
    path('toot', views.toot, name="toot"),
    path('reply/<int:id>', views.reply, name='reply'),
    path('redraft/<int:id>', views.redraft, name='redraft'),
    path('fav/<int:id>', views.fav, name='fav'),
    path('boost/<int:id>', views.boost, name='boost'),
    path('delete/<int:id>', views.delete, name='delete'),
    path('follow/<int:id>', views.follow, name='follow'),
    path('block/<int:id>', views.block, name='block'),
    path('mute/<int:id>', views.mute, name='mute'),
    path('search', views.search, name='search'),
    path('search_results', views.search_results, name='search_results'),
    path('emoji', views.emoji_reference, name='emoji'),
    path('pwabuilder-sw.js', views.service_worker, name="sw"),
    path('', views.home, name=''),
]
