from django.conf.urls import url

from verifications import views

urlpatterns = [
    # 图形验证码
    url(r'^image_codes/(?P<uuid>[\w-]+)/$', views.ImageCodeView.as_view()),
]