os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facebook_crm.settings')

app = Celery('facebook_crm')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
