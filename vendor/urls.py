from django.urls import path, include
from . import views
from accounts import views as accountViews

urlpatterns = [
    path('', accountViews.vendordashboard, name='vendor'),
    path('profile/', views.vprofile, name='vprofile'),
    path('menu_builder/', views.menu_builder, name='menu_builder'),
    path('menu_builder/category/<int:pk>/', views.fooditems_by_category, name='fooditems_by_category')
]