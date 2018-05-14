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
    path('home', views.home, name='home'),
    path('login', views.login, name="login"),
    path('logout', views.logout, name='logout'),
    path('oauth_callback', views.oauth_callback, name="oauth_callback"),
    path('error', views.error, name='error'),
    path('note', views.note, name='note'),
    path('local', views.local, name='local'),
    path('fed', views.fed, name='fed'),
    path('settings', views.settings, name='settings'),
    path('thread/<int:id>', views.thread, name='thread'),
    path('tags/<tag>', views.tag, name='tag'),
    path('user/<username>', views.user, name='user'),
    path('toot', views.toot, name="toot"),
    path('reply/<int:id>', views.reply, name='reply'),
    path('fav/<int:id>', views.fav, name='fav'),
    path('boost/<int:id>', views.boost, name='boost'),
    path('', views.home),
]
