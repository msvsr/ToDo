from django.urls import path

from . import views

app_name = 'ToDoApp'
urlpatterns = [
    path('all', views.todos, name='todos'),
    path('signup', views.signup, name='signup'),
    path('verifycode/<str:user>', views.verifycode, name='code'),
    path('resendverifycode/<str:user>', views.resendverifycode, name='resendcode'),
    path('create', views.create, name='create'),
    path('view/<str:todoid>', views.detail, name='detail'),
    path('delete/<str:todoid>', views.delete, name='delete'),
    path('update/<str:todoid>', views.update, name='update')
]