import json
import re

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse, HttpResponseBadRequest, \
    HttpResponseServerError
from django.shortcuts import render, redirect

from carts.utils import merge_cart_cookie_to_redis
from celery_tasks.email.tasks import send_verify_email
# Create your views here.
from django.urls import reverse
from django.views.generic.base import View

# pycharm不报错但是django不支持从工程文件开始寻找
# 所以下面这个不能用 要把apps设置标记为source root
# from meiduo_mall.apps.users.models import User
from django_redis import get_redis_connection

from goods.models import SKU
from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.utils.views import LoginRequiredMixin
from users.models import User, Address
import logging

logger = logging.getLogger('django')


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
        # return redirect(reverse('contents:index'))

        # 生成响应对象
        response = redirect(reverse('contents:index'))

        # 在响应对象中设置用户名信息
        # 将用户名写入到cookie,有效期15天
        response.set_cookie('username',user.username,max_age=3600*24*15)

        # 合并购物车
        response = merge_cart_cookie_to_redis(request=request, response=response)
        # 返回响应结果
        return response



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

class LoginView(View):
    """用户名登录"""

    def get(self, request):
        """提供登录界面的接口"""
        # 返回登录界面
        return render(request,'login.html')

    def post(self,request):
        """
        实现登录逻辑
        :param request:
        :return:
        """
        #接收参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        #校验参数
        if not all([username,password]):
            return HttpResponse('缺少必传参数')

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$',username):
            return HttpResponse('请输入正确的用户名或手机号')

        if not re.match(r'^[0-9A-Za-z]{8,20}$',password):
            return HttpResponse('密码最少8位,最长20位')

        # 认证登录用户
        user = authenticate(username=username,password=password)
        if user is None:
            return render(request,'login.html',{'account_errmsg':'用户名或密码错误'})

        # 实现状态保持
        login(request,user)

        # 设置状态保持的周期
        if remembered != 'on':
            # 不记住用户:浏览器会话结束就过期
            request.session.set_expiry(0)
        else:
            # 记住用户：None表示两周后过期
            request.session.set_expiry(None)

        #第一次修改------------
        # 响应登录结果
        # return redirect(reverse('contents:index'))

        #第二次修改------------
        # 生成相应对象
        # response = redirect(reverse('contents:index'))

        # 在响应对象中设置用户名信息
        # 将用户名写入到cookie,有效期15天
        # response.set_cookie('username',user.username,max_age=3600*24*15)

        # 返回响应对象
        # return response

        #第三次修改------------
        # 获取跳转过来的地址
        next = request.GET.get('next')
        # 判断参数是否存在
        if next:
            # 如果从别的页面跳转过来的,则重新跳转到原来的页面
            response = redirect(next)
        else:
            # 如果是直接登录成功,就重定向到首页
            response = redirect(reverse('contents:index'))

        # 设置cookie信息
        response.set_cookie('username',user.username,max_age=3600*24*15)

        # 合并购物车
        response = merge_cart_cookie_to_redis(request=request,response=response)
        # 返回响应
        return response

class LogoutView(View):
    """退出登录"""

    def get(self,request):
        """实现退出登录逻辑"""

        # 清理session
        logout(request)

        # 退出登录,重定向到登录页
        response = redirect(reverse('contents:index'))

        # 退出登录时清楚cookie中的username
        response.delete_cookie('username')

        # 返回响应
        return response




# 定义我们自己的类视图, 需要让它继承自: 工具类 + View
class UserInfoView(LoginRequiredMixin,View):
    """用户中心"""

    def get(self,request):
        """提供个人信息界面"""

        # 将验证用户的信息进行拼接
        context = {
            'username':request.user.username,
            'mobile':request.user.mobile,
            'email':request.user.email,
            'email_active':request.user.email_active
        }
        return render(request,'user_center_info.html',context=context)


class EmailView(LoginRequiredMixin,View):
    """添加邮箱"""

    def put(self,request):
        """实现添加邮箱逻辑"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 校验参数
        if not email:
            return HttpResponseForbidden('缺少email参数')
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return HttpResponseForbidden('参数email有误')

        # 赋值email字段
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            # DBERR = "5000"
            return JsonResponse({
                'code':RETCODE.DBERR,
                'errmsg':'添加邮箱失败'
            })


        # 异步发送验证邮件
        verify_url = request.user.generate_verify_email_url()
        send_verify_email.delay(email,verify_url)

        # 响应添加邮箱结果
        return JsonResponse({
            'code':RETCODE.OK,
            'errmsg':'添加邮箱成功'
        })



class VerifyEmailView(View):
    """验证邮箱"""

    def get(self,request):
        """实现邮箱验证逻辑"""
        # 接收参数
        token = request.GET.get('token')

        # 校验参数:判断token是否为空 或 过期,提取user
        if not token:
            return HttpResponseBadRequest('缺少token值')

        # 调用上面封装好的方法,将token传入
        user = User.check_verify_email_token(token)

        if not user:
            return HttpResponseForbidden('无效的token值')

        # 修改email_active的值为True
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return HttpResponseServerError('激活邮件失败')

        # 返回邮箱验证结果
        return redirect(reverse('users:info'))


class AddressView(LoginRequiredMixin,View):
    """用户收货地址"""

    def get(self,request):
        """提供收货地址界面"""
        return render(request,'user_center_site.html')


class CreateAddressView(LoginRequiredMixin, View):
    """新增地址"""

    def post(self,request):
        """实现新增地址逻辑"""

        # 获取地址个数
        count = Address.objects.filter(user_id=request.user.id,is_deleted=False).count()
        # 判断是否超过地址上线:最多20个
        if count >= 20:
            return JsonResponse({'code': RETCODE.THROTTLINGERR,
                                      'errmsg': '超过地址数量上限'})


        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return HttpResponseForbidden('参数email有误')


        # 保存地址信息
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )

            # 设置默认地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '新增地址失败'})


        # 新增地址成功,将新增的地址响应给前端实现局部刷新
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应保存结果
        return JsonResponse({'code': RETCODE.OK,
                             'errmsg': '新增地址成功',
                             'addresses': address_dict})


class AddressView(LoginRequiredMixin,View):
    """用户收货地址"""

    def get(self,request):
        """提供地址管理界面"""

        # 获取所有的地址
        addresses = Address.objects.filter(user=request.user,is_deleted=False)

        # 创建空的列表
        address_dict_list = []

        # 遍历
        for address in addresses:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }


            # 将默认地址移动到最前端
            default_address = request.user.default_address
            if default_address.id == address.id:
                # 查询集addresses没有insert方法
                address_dict_list.insert(0,address_dict)
            else:
                address_dict_list.append(address_dict)

        context = {
            'default_address_id':request.user.default_address_id,
            'addresses':address_dict_list
        }

        return render(request,'user_center_site.html',context)


class UpdateDestroyAddressView(LoginRequiredMixin, View):
    """修改和删除地址"""

    def put(self, request, address_id):
        """修改地址"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseForbidden('参数mobile有误')
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return HttpResponseForbidden('参数email有误')

        # 判断地址是否存在,并更新地址信息
        try:
            Address.objects.filter(id=address_id).update(
                user = request.user,
                title = receiver,
                receiver = receiver,
                province_id = province_id,
                city_id = city_id,
                district_id = district_id,
                place = place,
                mobile = mobile,
                tel = tel,
                email = email
            )
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR,
                                      'errmsg': '更新地址失败'})

        # 构造响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应更新地址结果
        return JsonResponse({'code': RETCODE.OK,
                                  'errmsg': '更新地址成功',
                                  'address': address_dict})

    def delete(self, request, address_id):
        """删除地址"""
        try:
            # 查询要删除的地址
            address = Address.objects.get(id=address_id)

            # 将地址逻辑删除设置为True
            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '删除地址失败'})

        # 响应删除地址结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '删除地址成功'})


class DefaultAddressView(LoginRequiredMixin, View):
    """设置默认地址"""

    def put(self, request, address_id):
        """设置默认地址"""
        try:
            # 接收参数,查询地址
            address = Address.objects.get(id=address_id)

            # 设置地址为默认地址
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置默认地址失败'})

        # 响应设置默认地址结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '设置默认地址成功'})


class UpdateTitleAddressView(LoginRequiredMixin, View):
    """设置地址标题"""

    def put(self, request, address_id):
        """设置地址标题"""
        # 接收参数：地址标题
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        try:
            # 查询地址
            address = Address.objects.get(id=address_id)

            # 设置新的地址标题
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': RETCODE.DBERR, 'errmsg': '设置地址标题失败'})

        # 4.响应删除地址结果
        return JsonResponse({'code': RETCODE.OK, 'errmsg': '设置地址标题成功'})


class ChangePasswordView(LoginRequiredMixin, View):
    """修改密码"""

    def get(self, request):
        """展示修改密码界面"""
        return render(request, 'user_center_pass.html')

    def post(self, request):
        """实现修改密码逻辑"""
        # 接收参数
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        new_password2 = request.POST.get('new_password2')

        # 校验参数
        if not all([old_password, new_password, new_password2]):
            return HttpResponseForbidden('缺少必传参数')

        # check_password返回bool值:True or False
        flag = request.user.check_password(old_password)

        if flag == True:
            if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
                return HttpResponseForbidden('密码最少8位，最长20位')
            if new_password != new_password2:
                return HttpResponseForbidden('两次输入的密码不一致')

            # 修改密码
            try:
                request.user.set_password(new_password)
                request.user.save()
            except Exception as e:
                logger.error(e)
                return render(request, 'user_center_pass.html', {'change_pwd_errmsg': '修改密码失败'})

            # 清理状态保持信息
            logout(request)
            response = redirect(reverse('users:login'))
            response.delete_cookie('username')

            # # 响应密码修改结果：重定向到登录界面
            return response

        else:
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码错误'})


class UserBrowseHistory(LoginRequiredMixin,View):
    """用户浏览记录"""

    def get(self,request):
        """获取用户浏览记录"""
        redis_conn = get_redis_connection('history')
        sku_ids = redis_conn.lrange('history_%s' % request.user.id,0,-1)

        # 根据sku_ids列表数据,查询出商品sku信息
        skus = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            skus.append({
                'id':sku.id,
                'name':sku.name,
                'default_image_url':sku.default_image_url,
                'price':sku.price
            })

        return JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'skus': skus})


    def post(self,request):
        """保存用户浏览记录"""
        # 接收参数
        json_dict = json.loads(request.body)
        sku_id = json_dict.get('sku_id')


        # 校验参数
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            HttpResponseForbidden('sku不存在')

        # 保存用户浏览数据
        redis_conn = get_redis_connection('history')

        pl = redis_conn.pipeline()

        user_id = request.user.id


        # 先去重:这里给0代表去除所有的sku_id
        pl.lrem('history_%s' % user_id,0,sku_id)

        # 再存储
        pl.lpush('history_%s' % user_id,sku_id)

        # 最后截取
        pl.ltrim('history_%s' % user_id,0,4)

        # 执行管道
        pl.execute()

        # 响应结果
        return JsonResponse({
            'code':RETCODE.OK,
            'errmsg':'OK'
        })