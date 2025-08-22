from django.urls import path
from . import views
from . import interview_view

urlpatterns = [
    path('', views.index, name='index'),
    path('process/', views.process_resume, name='process_resume'),
    path('match/', views.match_analysis, name='match_analysis'),
    path('save/', views.save_resume, name='save_resume'),
    path('latest/', views.get_latest_resume, name='latest_resume'),
    path('history/', views.get_resume_history, name='resume_history'),
    path('cover-letter/', views.cover_letter_generator_custom, name='cover_letter_generator_custom'),
    # Add cover-letters endpoints to match frontend expectations
    path('cover-letters/generate/', views.cover_letter_generator_custom, name='cover_letter_generate'),
    path('cover-letters/regenerate/', views.cover_letter_generator_custom, name='cover_letter_regenerate'),
    path('cover-letters/history/', views.get_cover_letter_history, name='cover_letter_history'),
    path('user-stats/', views.user_stats, name='user_stats'),
    path('interview/start/', interview_view.start_interview, name='start_interview'),
    path('interview/respond/', interview_view.response_to_question, name='respond_to_question'),
    path('interview/status/<str:user_id>/', interview_view.interview_status, name='interview_status'),
]

