from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('blog/', views.blog, name='blog'),
    path('news/', views.news_list, name='news'),
    path('article/<int:pk>/', views.article_detail, name='article_detail'),
    
    # 2FA URLs
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('setup-2fa/', views.setup_2fa, name='setup_2fa'),
    path('profile/', views.profile_view, name='profile'),
    path('disable-2fa/', views.disable_2fa, name='disable_2fa'),
    path('logout/', views.logout_view, name='logout'),
    path('password-change/', views.password_change_view, name='password_change'),
    path('chatbot/', views.chatbot_view, name='chatbot'),
]