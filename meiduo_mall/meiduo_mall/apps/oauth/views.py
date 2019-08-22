import re

from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django.contrib.auth import login
from django.db import DatabaseError
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import render, redirect
import logging
# Create your views here.
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from meiduo_mall.utils.response_code import RETCODE
from oauth.models import OAuthQQUser
from oauth.utils import generate_access_token, check_access_token
from users.models import User

logger = logging.getLogger('django')

class QQURLView(View):
    """提供QQ登录页面网址"""

    def get(self,request):
        # next表示从哪个页面进入到的登录页面,将来登陆成功后,就自动回到这个页面
        next = request.GET.get('next')

        # 获取QQ登录页面网址
        # 创建OAuthQQ类的对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URL,
                        state=next)

        # 调用对象的获取QQ地址方法
        login_url = oauth.get_qq_url()

        # 返回登录地址
        return JsonResponse({
            'code':RETCODE.OK,
            'errmsg':'OK',
            'login_url':login_url
        })


class QQUserView(View):
    """用户扫码登录的回调处理"""

    def get(self,request):
        """Oauth2.0认证"""

        #接收Authorization Code
        code = request.GET.get('code')

        if not code:
            return HttpResponseForbidden('缺少code')

        # 创建工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URL)

        try:
            # 携带code向QQ服务器请求access_token
            access_token = oauth.get_access_token(code)

            # 携带access_token向QQ服务器请求openid
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            # 如果上面获取openid出错,则验证失败
            logger.error(e)

            #返回结果
            return HttpResponseServerError('OAuth2.0认证失败')


        try:
            #查看是否有openid对应的用户
            oauth_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 如果openid没绑定美多商城用户
            # 调用我们封装好的方法,对openid进行加密,生成access_token字符串
            access_token = generate_access_token(openid)
            # 拿到access_token字符串后,拼接字典
            context = {'access_token':access_token}
            # 返回响应,重新渲染
            return render(request,'oauth_callback.html',context)
        else:
            # 如果openid已绑定美多商城用户
            # 根据user外键,获取对应的QQ用户
            qq_user = oauth_user.user
            # 实现状态保持
            login(request,qq_user)

            # 创建重定向到主页的对象
            response = redirect(reverse('contents:index'))

            # 将用户信息写入到cookie中,有效期15天
            response.set_cookie('username',qq_user,max_age=3600*24*15)

            # 返回响应
            return response


    def post(self,request):
        """美多商城用户绑定到openid"""

        # 1.接收参数
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        sms_code_client = request.POST.get('sms_code')
        access_token = request.POST.get('access_token')

        # 2.校验参数
        # 判断参数是否齐全
        if not all([mobile,password,sms_code_client]):
            return HttpResponseForbidden('缺少必传参数')

        # 判断手机是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('请输入正确的手机号码')

        # 判断密码是否合格
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return HttpResponseForbidden('请输入8-20位的密码')

        # 3.判断短信验证码是否一致
        # 创建redis连接对象
        redis_conn = get_redis_connection('verify_code')
        # 从redis中获取sms_code值
        sms_code_server = redis_conn.get('sms_code_%s'%mobile)
        # 判断获取的sms_code是否存在
        if sms_code_server is None:
            # 如果没有,直接返回
            return render(request,'oauth_callback.html',{'sms_code_errmsg':'无效的短信验证码'})
        # 如果有,则进行判断
        if sms_code_client != sms_code_server.decode():
            # 如果不匹配,则直接返回
            return render(request,'oauth_callback.html',{'sms_code_errmsg': '输入短信验证码有误'})

        # 调用我们自定义的函数,检验传入的access_token是否正确
        # 错误提示放在sms_code_errmsg位置
        openid = check_access_token(access_token)
        if not openid:
            return render(request,'oauth_callback.html',{'openid_errmsg': '无效的openid'})

        # 4.保存注册数据
        try:
            user =User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 用户不存在,新建用户
            user = User.objects.create_user(username=mobile,password=password,mobile=mobile)
        else:
            # 如果用户存在,检查密码
            if not user.check_password(password):
                return render(request,'oauth_callback.html', {'account_errmsg': '用户名或密码错误'})


        # 5.将用户绑定openid
        try:
            OAuthQQUser.objects.create(openid=openid,user=user)
        except DatabaseError:
            return render(request, 'oauth_callback.html', {'qq_login_errmsg': 'QQ登录失败'})

        # 6.实现状态保持
        login(request,user)

        # 7.响应绑定结果
        next = request.GET.get('state')
        response = redirect(next)

        # 8.登录时用户名写入到cookie,有效期15天
        response.set_cookie('username',user.username,max_age=3600*24*15)

        # 9.响应
        return response