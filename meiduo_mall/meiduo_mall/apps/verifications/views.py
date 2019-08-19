from django.db.models import constants
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views.generic.base import View
from django_redis import get_redis_connection

from meiduo_mall.libs.captcha import captcha


class ImageCodeView(View):
    """图形验证码"""

    def get(self, request, uuid):
        """
        :param request: 请求对象
        :param uuid: 唯一标识图形验证码所属于的用户
        :return: image/jpg
        """
        # 生成图片验证码
        text,image = captcha.generate_captcha()

        # 保存图片验证码
        redis_conn = get_redis_connection('verfy_code')

        # 图形验证码有效期，单位：秒
        # IMAGE_CODE_REDIS_EXPIRES = 300
        redis_conn.setex('img_%s' % uuid,constants.IMAGE_CODE_REDIS_EXPIRES,text)

        # 响应图片验证码
        return HttpResponse(image,content_type='image/jpg')