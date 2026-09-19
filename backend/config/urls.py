"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path(
        'admin/',
        admin.site.urls,
    ),

    path(
        'api/v1/auth/',
        include('apps.users.urls'),
    ),

    path(
        'api/v1/profile/',
        include('apps.profiles.urls'),
    ),

    path(
        'api/v1/exams/',
        include('apps.exams.urls'),
    ),

    path(
        'api/v1/questions/',
        include('apps.questions.urls'),
    ),

    path(
        'api/v1/writing/',
        include('apps.writing.urls'),
    ),

    path(
        'api/v1/speaking/',
        include('apps.speaking.urls'),
    ),

    path(
        'api/v1/vocabulary/',
        include('apps.vocabulary.urls'),
    ),

    path(
        'api/v1/grammar/',
        include('apps.grammar.urls'),
    ),

    path(
        'api/v1/learning/',
        include('apps.learning.urls'),
    ),

    path(
        'api/v1/adaptive/',
        include('apps.adaptive.urls'),
    ),

    path(
        'api/v1/analytics/',
        include('apps.analytics.urls'),
    ),
]
