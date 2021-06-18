from django.urls import path

from . import views

app_name = 'ToDoApp'
urlpatterns = [
    path('', views.todos, name='todos'),
    path('<str:todoid>/', views.detail, name='detail'),
    path('<str:todoid>/delete', views.delete, name='delete')
]