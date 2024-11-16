from django.urls import path
from .import views
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated


urlpatterns = [
    path('login/', views.login_page, name='login_page'),
    path('api/login/', (views.LoginView.as_view()), name='login-api'),
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup_view'),
    path('api/signup/', (views.SignupView.as_view()), name='signup'),
    path('upload_form/', login_required(views.upload_data), name='upload_form'),
    path('api/upload/', login_required(views.FileUploadView.as_view()), name='upload_data'),
    path('query_builder/', login_required(views.query_builder), name='query_builder'),
    path('api/query/', login_required(views.QueryDataView.as_view()), name='query-data'),
    path('api/get-states/<str:country>/', login_required(views.StateListView.as_view()), name='get-states'),
    path('api/get-cities/<str:state>/', login_required(views.CityListView.as_view()), name='get-cities'),
    path('logout/', views.logout_view, name='logout'),
    path('users/', login_required(views.UserListView.as_view()), name='users'),
    path('delete/<int:user_id>/', login_required(views.delete_user), name='delete_user'),
]