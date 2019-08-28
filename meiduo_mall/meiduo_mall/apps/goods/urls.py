from django.conf.urls import url

from goods import views

urlpatterns = [
    # 商品列表页
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', views.ListView.as_view(), name='list'),
    # 热销商品排行
    url(r'^hot/(?P<category_id>\d+)/$', views.HotGoodsView.as_view()),
]