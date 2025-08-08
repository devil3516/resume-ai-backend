from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomTokenObtainPairView, RegisterView, UserProfileView, UpdateUserView, change_password, logout, get_user_progress, update_user_progress

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', logout, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('profile/update/', UpdateUserView.as_view(), name='update_profile'),
    path('change-password/', change_password, name='change_password'),
    path('progress/', get_user_progress, name='user_progress'),
    path('progress/update/', update_user_progress, name='update_progress'),
] 