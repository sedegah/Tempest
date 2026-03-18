from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('features/', views.features_view, name='features'),
    path('how-it-works/', views.how_it_works_view, name='how_it_works'),
    path('tech-stack/', views.tech_stack_view, name='tech_stack'),
    path('upload/', views.upload_view, name='upload'),
    path('success/<str:token>/<uuid:original_uuid>/', views.success_view, name='success'),
    path('download/<str:token>/<uuid:original_uuid>/', views.download_view, name='download'),
    path('perform-download/<str:token>/<uuid:original_uuid>/', views.perform_download, name='perform_download'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('terms/', views.terms_view, name='terms'),
    path('documentation/', views.documentation_view, name='documentation'),
    path('api-reference/', views.api_reference_view, name='api_reference'),
]
