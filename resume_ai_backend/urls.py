from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include("resume_api.urls")),
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/resumes/", include("resume_api.urls")),
   
]
