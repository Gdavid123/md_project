from django.conf.urls import url

from meiduo_mall.apps.users import views

urlpatterns = [
    url(r'^register/$',views.RegisterView.as_view(),name='register'),
# 判断用户名是否重复
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),
# 判断手机号是否重复
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
]