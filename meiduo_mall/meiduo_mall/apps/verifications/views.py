import random

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views.generic.base import View
from django_redis import get_redis_connection

from celery_tasks.sms.tasks import send_sms_code
from meiduo_mall.libs.captcha.captcha import captcha
from meiduo_mall.libs.yuntongxun.ccp_sms import CCP
from meiduo_mall.utils.response_code import RETCODE
from verifications import constants
import logging

logger = logging.getLogger('django')

class ImageCodeView(View):
    """图形验证码"""

    def get(self, request, uuid):
        """
        :param request: 请求对象
        :param uuid: 唯一标识图形验证码所属于的用户
        :return: image/jpg
        """
        # 生成图片验证码 text是保存的验证码  images返回给前端
        text,image = captcha.generate_captcha()

        # 连接redis,指定dev中设置的库名
        redis_conn = get_redis_connection('verify_code')

        # 保存图片验证码, 设置图形验证码有效期，单位：秒
        # IMAGE_CODE_REDIS_EXPIRES = 300  常量保存在constants.py文件中
        redis_conn.setex('img_%s' % uuid,constants.IMAGE_CODE_REDIS_EXPIRES,text)

        # 响应图片验证码
        return HttpResponse(image,content_type='image/jpg')


class SMSCodeView(View):
    """短信验证码"""

    def get(self, reqeust, mobile):
        """
        :param reqeust: 请求对象
        :param mobile: 手机号
        :return: JSON
        """
        # 3.创建连接到redis的对象
        redis_conn = get_redis_connection('verify_code')

        flag = redis_conn.get('send_flag_%s' % mobile)
        if flag:
            return JsonResponse({
                'code':RETCODE.THROTTLINGERR,
                'errmsg':'发送短信过于频繁'
            })

        # 1.接收参数
        image_code_client = reqeust.GET.get('image_code')
        uuid = reqeust.GET.get('image_code_id')

        # 2.校验参数
        if not all([image_code_client,uuid]):
            return JsonResponse({
                'code':RETCODE.NECESSARYPARAMERR,
                'errmsg':'缺少必传参数'
            })



        # 4.提取图形验证码
        image_code_server = redis_conn.get('img_%s' % uuid)
        if image_code_server is None:
            # 图形验证码过期或者不存在
            return JsonResponse({
                'code':RETCODE.IMAGECODEERR,
                'errmsg':'图形验证码失效'
            })

        # 5.删除图形验证码,避免恶意测试图形验证码
        try:
            redis_conn.delete('img_%s' % uuid)
        except Exception as e:
            logger.error(e)

        # 6.对比图形验证码
        # bytes转字符串
        image_code_server = image_code_server.decode()
        # 转小写后比较
        if image_code_client.lower() != image_code_server.lower():
            return JsonResponse({
                'code':RETCODE.IMAGECODEERR,
                'errmsg':'输入图形验证码有误'
            })

        # 7.生成短信验证码：生成6位数验证码
        sms_code = '%06d' % random.randint(0,999999)
        logger.info(sms_code)

        # 8.保存短信验证码
        # 短信验证码有效期,单位：秒
        # SMS_CODE_REDIS_EXPIRES = 300
        # 创建Redis管道
        pl = redis_conn.pipeline()

        # 将Redis请求添加到队列
        pl.setex('sms_code_%s' % mobile,constants.SMS_CODE_REDIS_EXPIRES,sms_code)

        pl.setex('send_flag_%s' % mobile,60,1)

        #执行请求
        pl.execute()

        # 9.发送短信验证码
        # 短信模板
        # SMS_CODE_REDIS_EXPIRES // 60 = 5min
        # SEND_SMS_TEMPLATE_ID = 1
        # CCP().send_template_sms(mobile,[sms_code,5],constants.SEND_SMS_TEMPLATE_ID)
        # send_sms_code.delay(mobile,sms_code)

        # 10.响应结果
        return JsonResponse({
            'code':RETCODE.OK,
            'errmsg':'发送短信成功'
        })