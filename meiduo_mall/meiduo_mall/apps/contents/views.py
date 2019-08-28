from django.shortcuts import render

# Create your views here.
from django.views.generic.base import View
from contents.models import ContentCategory
from goods.utils import get_categories

class IndexView(View):
    """首页广告"""

    def get(self, request):
        """
        展示首页内容
        :param request:
        :return:
        """
        # 返回多级菜单
        categories = get_categories()

        dict = {}
        # 获取广告对应的类别
        content_categories = ContentCategory.objects.all()

        for cat in content_categories:
            dict[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

        context = {
            'categories':categories,
            'contents':dict
        }

        return render(request,'index.html',context)