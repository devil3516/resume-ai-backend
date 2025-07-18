from django.urls import path
from . import views
from .views import process_resume, save_resume, get_latest_resume, get_resume_history

urlpatterns = [
    path('', views.index, name='index'),
    path('process/', views.process_resume, name='process_resume'),
    path('match/', views.match_analysis, name='match_analysis'),
    path('resumes/process/', process_resume, name='process_resume'),  # existing
    path('resumes/save/', save_resume, name='save_resume'),
    path('resumes/latest/', get_latest_resume, name='latest_resume'),
    path('resumes/history/', get_resume_history, name='resume_history'),

]

