from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path('', views.calendar_home_view, name="calendar-home"),
    path('authorize/', views.authorize, name='authorize'),
    path('oauth2callback/', views.oauth2callback, name='oauth2callback'),
    path('add-event/', views.add_event_page, name='add-event'),
    path('list-calendars/', views.list_calendars, name='list-calendars'),
]
