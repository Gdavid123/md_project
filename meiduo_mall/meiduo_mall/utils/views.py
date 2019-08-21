from django.contrib.auth.decorators import login_required

# 添加扩展类:
# 因为这类扩展其实就是 Mixin 扩展类的扩展方式
# 所以我们起名时, 最好也加上 Mixin 字样, 不加也可以.
class LoginRequiredMixin(object):
    """验证用户是否登录的工具类"""

    # 重写as_view()函数
    @classmethod
    def as_view(cls,**initkwargs):
        # 调用父类的as_view()方法
        view = super().as_view()
        # 添加装饰行为
        return login_required(view)