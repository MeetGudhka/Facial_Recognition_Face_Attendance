

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('start_attendance/', views.start_attendance, name='start_attendance'),
    path('view_attendance/', views.view_attendance, name='view_attendance'),  # <-- New route
]
