from django.urls import path
from accounts import views as AccountViews
from customers import views

urlpatterns = [
    path('', AccountViews.custdashboard, name='customer'),
    path('profile/', views.cprofile, name='cprofile'),
]