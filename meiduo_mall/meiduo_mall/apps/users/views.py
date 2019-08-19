from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views.generic.base import View

# from meiduo_mall.apps.users.models import User


class RegisterView(View):
    """用户注册"""

    def get(self,request):
        """
        提供注册界面
        :param request: 请求对象
        :return: 注册界面
        """
        return render(request,'register.html')


# class UsernameCountView(View):
#     """判断用户名是否重复注册"""
#
#     def get(self,request,username):
#         """
#
#         :param request:
#         :param username:用户名
#         :return:JSON
#         """
#         # 获取数据库中该用户名对应的个数
#         count = User.objects.filter(username=username).count()
#
#         # 拼接参数,返回:
#         return JsonResponse({'code':RETCODE.OK,'errmsg':'OK','count':count})