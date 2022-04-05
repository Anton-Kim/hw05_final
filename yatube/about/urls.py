from django.urls import path

from . import views


app_name = 'about'

urlpatterns = [
    path('author/', views.About_author.as_view(), name='author'),
    path('tech/', views.About_tech.as_view(), name='tech'),
]
