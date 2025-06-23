from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('sync-data/', views.sync_facebook_data, name='sync_data'),
]
