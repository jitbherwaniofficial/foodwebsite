from django.urls import path, include
from . import views
from accounts import views as accountViews

urlpatterns = [
    path('', accountViews.vendordashboard, name='vendor'),
    path('profile/', views.vprofile, name='vprofile'),
    
]