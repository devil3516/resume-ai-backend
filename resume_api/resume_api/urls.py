from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('process/', views.process_resume, name='process_resume'),
    path('match/', views.match_analysis, name='match_analysis'),
] 