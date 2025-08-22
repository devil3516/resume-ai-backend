from django.urls import path
from .views import start_interview, response_to_question, interview_status

urlpatterns = [
    path('interview/start/', start_interview, name='start_interview'),
    path('interview/respond/', response_to_question, name='respond_to_question'),
    path('interview/status/<str:user_id>/', interview_status, name='interview_status'),
]