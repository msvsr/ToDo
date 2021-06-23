from django.urls import path

from . import views

app_name = 'ToDoApp'
urlpatterns = [
    path('all', views.todos, name='todos'),
    path('signin', views.signin, name='signin'),
    path('signup', views.signup, name='signup'),
    path('logout', views.log_out, name="logout"),
    path('askforlogout', views.ask_for_logout, name="askforlogout"),
    path('forgotpassword', views.forgot_password, name="forgotpassword"),
    path("confirmforgotpassword", views.confirm_forgot_password, name="confirmforgotpassword"),
    path('verifycode/<str:user>', views.verifycode, name='code'),
    path('resendverifycode/<str:user>', views.resendverifycode, name='resendcode'),
    path('proccedsignin/<str:user>', views.proceedsignin, name='proceedsignin'),
    path('create', views.create, name='create'),
    path('view/<str:todo_id>', views.detail, name='detail'),
    path('delete/<str:todo_id>', views.delete, name='delete'),
    path('update/<str:todo_id>', views.update, name='update')
]