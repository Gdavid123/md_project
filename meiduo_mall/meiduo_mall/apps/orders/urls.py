from django.conf.urls import url

from orders import views

urlpatterns = [
    # 订单确认
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view(), name='settlement'),
    # 订单提交
    url(r'^orders/commit/$', views.OrderSettlementView.as_view()),
    # 订单提交成功过渡页面
    url(r'^orders/success/$', views.OrderSuccessView.as_view()),
    # 我的订单
    url(r'^orders/info/(?P<page_num>\d+)/$', views.UserOrderInfoView.as_view(), name='info'),
]