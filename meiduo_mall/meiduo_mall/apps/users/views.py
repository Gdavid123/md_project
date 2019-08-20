import re

from django.contrib.auth import login
from django.db import DatabaseError
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views.generic.base import View

# pycharm不报错但是django不支持从工程文件开始寻找
# 所以下面这个不能用 要把apps设置标记为source root
# from meiduo_mall.apps.users.models import User
from django_redis import get_redis_connection

from users.models import User


class RegisterView(View):
    """用户注册"""

    def get(self,request):
        """
        提供注册界面
        :param request: 请求对象
        :return: 注册界面
        """
        return render(request,'register.html')

    def post(self,request):
        """
        实现注册
        :param request:请求对象
        :return:注册结果
        """
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')
        sms_code_client = request.POST.get('sms_code')

        # 校验信息
        if not all([username,password,password2,mobile,allow]):
            return HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$',username):
            return HttpResponseForbidden('请输入5-20个字符的用户名')

        if not re.match(r'^[0-9A-Za-z]{8,20}$',password):
            return HttpResponseForbidden('请输入8-20位的密码')

        if password != password2:
            return HttpResponseForbidden('两次输入的密码不一致')

        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return HttpResponseForbidden('请输入正确的手机号码')

        if allow != 'on':
            return HttpResponseForbidden('请勾选用户协议')

        #获取redis连接对象
        redis_conn = get_redis_connection('verify_code')
        #从redis中获取保存的sms_code
        sms_code_server = redis_conn.get('sms_code_%s' % mobile)
        #判断sms_code_server是否存在
        if sms_code_server is None:
            #不存在直接返回,说明服务器的验证码过期了,超时
            return  render(request,'register.html',{'sms_code_errmsg':'无效的短信验证码'})
        #如果sms_code_server存在,则对比两者:
        if sms_code_client != sms_code_server.decode():
            #对比失败,说明短信验证码有问题,直接返回:
            return render(request,'register.html',{'sms_code_errmsg':'输入短信验证码有误'})

        try:
            user = User.objects.create_user(username=username,password=password,mobile=mobile)
        except DatabaseError:
            return render(request,'register.html',{'register_errmsg': '注册失败'})

        # 实现状态保持
        login(request, user)

        # 响应注册结果
        return redirect(reverse('contents:index'))


class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self,request,username):
        """

        :param request:
        :param username:用户名
        :return:JSON
        """
        # 获取数据库中该用户名对应的个数
        count = User.objects.filter(username=username).count()

        # 拼接参数,返回:
        return JsonResponse({'code':0,'errmsg':'OK','count':count})

class MobileCountView(View):
    """判断手机号是否重复注册"""

    def get(self, request, mobile):
        """
        :param request: 请求对象
        :param mobile: 手机号
        :return: JSON
        """
        count = User.objects.filter(mobile=mobile).count()
        return JsonResponse({'code': 0, 'errmsg': 'OK', 'count': count})