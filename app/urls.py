from django.urls import path
from app import views

urlpatterns = [
    path('', views.index, name='index'), #代表url打 http://127.0.0.1:8000/test_app/home才會進到test_app, 因為prject在home
    path('profile/', views.profile, name='profile'), #代表url打 http://127.0.0.1:8000/test_app/home才會進到test_app, 因為prject在home
    # path('qrcode', views.qrcode, name='qrcode'),
    # path('command/<str:movie_name>/', views.save_movie_name, name='get_movie_name'),
    # path('command/get_all_movie', views.get_all_data, name='get_all_data'),
    path('upload_image', views.upload_image, name='upload_image'),
    path('save_meal', views.save_meal, name='save_meal'),
    path('get_recent_meals', views.get_recent_meals, name='get_recent_meals'),
    path('get_month_meals', views.get_month_meals, name='get_month_meals'),
    path('save_user', views.save_user, name='save_user'),
]
