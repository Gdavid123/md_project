from django.shortcuts import render

# Create your views here.
from django.views.generic.base import View


class IndexView(View):
    """首页广告"""

    def get(self, request):
        """提供首页广告界面"""
        return render(request, 'index.html')