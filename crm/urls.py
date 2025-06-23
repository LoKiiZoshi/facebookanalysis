from django.urls import path
from . import views, debug_views

app_name = 'crm'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('sync-data/', views.sync_facebook_data, name='sync_data'),
    path('debug-api/', debug_views.debug_facebook_api, name='debug_api'),
    path('test-page/<str:page_id>/', debug_views.test_page_access, name='test_page'),
]
