from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('process/', views.process_resume, name='process_resume'),
    path('match/', views.match_analysis, name='match_analysis'),
    path('save/', views.save_resume, name='save_resume'),
    path('latest/', views.get_latest_resume, name='latest_resume'),
    path('history/', views.get_resume_history, name='resume_history'),
    path('cover-letter/', views.cover_letter_generator_custom, name='cover_letter_generator_custom'),
]

