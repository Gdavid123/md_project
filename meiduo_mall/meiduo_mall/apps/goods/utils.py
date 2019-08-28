from collections import OrderedDict

from goods.models import GoodsChannel


def get_categories():
    """
    获取商城商品分类菜单
    :return:
    """
    # 1. 创建有序字典
    categories = OrderedDict()

    # 2.获取所有频道
    channels = GoodsChannel.objects.order_by('group_id','sequence')

    # 3.遍历拿取每一个频道
    for channel in channels:

        # 4.根据拿取的频道,获取对应的频道组id
        group_id = channel.group_id
        # 5.判断频道组id在不在有序字典中
        if group_id not in categories:
            # 6.没有则添加;基本结构创建好
            categories[group_id] = {'channels':[],'sub_cats':[]}

        # 7.根据频道的外键 获取一级类别
        cat1 = channel.category

        # 8.把一级类别对应的数据添加 channe对应的列表中
        categories[group_id]['channels'].append({
            'id':cat1.id,
            'name':cat1.name,
            'url':channel.url
        })



        # 9.获取二级和三级数据,添加
        for cat2 in cat1.goodscategory_set.all():
            cat2.sub_cats = []
            for cat3 in cat2.goodscategory_set.all():
                cat2.sub_cats.append(cat3)

            categories[group_id]['sub_cats'].append(cat2)

    # 10.返回有序字典
    return categories



def get_breadcrumb(category):
    """
    获取面包屑导航
    :param category: 商品类别
    :return: 面包屑导航字典
    """

    # 定义一个字典:
    breadcrumb = dict(
        cat1='',
        cat2='',
        cat3=''
    )

    # 判断category是哪一个级别的
    # 注意:这里的category是GoodsCategory对象
    if category.parent is None:
        # 当前类别为一级类别
        breadcrumb['cat1'] = category

    #因为当前这个表示自关联表,所以关联的对象还是自己
    elif category.goodscategory_set.count() ==0:
        #当前类别为三级
        breadcrumb['cat3'] = category
        breadcrumb['cat2'] = category.parent
        cat2 = category.parent
        breadcrumb['cat1'] = cat2.parent

    else:
        # 当前类别为二级
        breadcrumb['cat2'] = category
        breadcrumb['cat1'] = category.parent

    return breadcrumb
