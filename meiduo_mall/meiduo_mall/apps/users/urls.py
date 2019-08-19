from django.conf.urls import url, include

from meiduo_mall.apps.users import views

urlpatterns = [
    url(r'^register/$',views.RegisterView.as_view(),name='register'),
# 判断用户名是否重复
#     url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),
]