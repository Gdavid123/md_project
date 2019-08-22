from itsdangerous import TimedJSONWebSignatureSerializer, BadData
from django.conf import settings

from verifications import constants


def generate_access_token(openid):
    """
    签名openid
    :param openid: 用户的openid
    :return: access_token
    """

    #QQ登录保存用户数据的token有效期
    #settings.SECRET_KEY   加密使用的秘钥
    #SAVE_QQ_USER_TOKEN_EXPIRES = 600  过期时间
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                                 expires_in=constants.ACCESS_TOKEN_EXPIRES)

    data = {'openid':openid}
    # 连同字典加密
    token = serializer.dumps(data)

    return token.decode()

# 定义函数,检验传入的access_token里面是否包含openid
def check_access_token(access_token):
    """
    检验用户传入的token
    :param access_token: token
    :return: openid or None
    """

    # 调用itsdangerous中的类,生成对象
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                                 expires_in=constants.SAVE_QQ_USER_TOKEN_EXPIRES)

    try:
        # 尝试使用对象的loads函数
        # 对access_token进行反序列化(解密)
        # 查看是否能够获取到数据
        data = serializer.loads(access_token)

    except BadData:
        # 如果出错,则说明access_token里面不是我们认可的
        # 返回None
        return None

    else:
        # 如果能够从中获取data,则把data中的openid返回
        return data.get('openid')