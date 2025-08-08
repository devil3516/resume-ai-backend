from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='resume_index'),
    path('test/', views.test_routing, name='resume_test'),
    path('process/', views.process_resume, name='resume_process'),
    path('match/', views.match_analysis, name='resume_match'),
    path('save/', views.save_resume, name='resume_save'),
    path('latest/', views.get_latest_resume, name='resume_latest'),
    path('history/', views.get_resume_history, name='resume_history'),
]

