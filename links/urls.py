from django.urls import path
from . import views

app_name = 'links'

urlpatterns = [
    path('<str:code>/', views.short_redirect_view, name='redirect'),
]
