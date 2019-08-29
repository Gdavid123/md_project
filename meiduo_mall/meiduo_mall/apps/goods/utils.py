from collections import OrderedDict

from django.shortcuts import render

from goods.models import GoodsChannel, SKU


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



def get_goods_and_spec(sku_id,request):
    # 获取当前sku信息
    try:
        sku = SKU.objects.get(id=sku_id)
        sku.image= sku.skuimage_set.all()
    except SKU.DoesNotExist:
        return render(request,'404.html')


    # 面包屑导航信息中的频道
    goods = sku.goods

    # 构建当前商品的规格键
    sku_specs = sku.skuspecification_set.order_by('spec_id')

    sku_key = []

    for spec in sku_specs:
        sku_key.append(spec.option.id)


    # 获取当前商品类的所有商品个体
    skus = goods.sku_set.all()


    # 构建不同规格参数的sku字典
    # spec_sku_map = {
    #     (规格1参数id, 规格2参数id, 规格3参数id, ...): sku_id,
    #     (规格1参数id, 规格2参数id, 规格3参数id, ...): sku_id,
    #     ...
    # }
    spec_sku_map = {}

    for s in skus:
        # 获取sku的规格参数
        s_specs = s.skuspecification_set.order_by('spec_id')

        # 用于形成规格参数-sku字典的键
        key = []

        for spec in s_specs:
            key.append(spec.option.id)

        # 向规格参数-sku字典添加记录
        spec_sku_map[tuple(key)] = s.id

    # 获取当前商品的规格信息
    # specs = [
    #    {
    #        'name': '屏幕尺寸',
    #        'options': [
    #            {'value': '13.3寸', 'sku_id': xxx},
    #            {'value': '15.4寸', 'sku_id': xxx},
    #        ]
    #    },
    #    {
    #        'name': '颜色',
    #        'options': [
    #            {'value': '银色', 'sku_id': xxx},
    #            {'value': '黑色', 'sku_id': xxx}
    #        ]
    #    },
    #    ...
    # ]
    goods_specs = goods.goodsspecification_set.order_by('id')

    # 若当前sku的规格信息不完整,则不再继续
    if len(sku_key) < len(goods_specs):
        return

    for index,spec in enumerate(goods_specs):
        # 复制当前sku的规格键
        key = sku_key[:]

        # 该规格的选项
        spec_options = spec.specificationoption_set.all()

        for option in spec_options:
            # 再规格参数sku字典中查找符合当前规格的sku
            key[index] = option.id
            option.sku_id = spec_sku_map.get(tuple(key))

        spec.spec_options = spec_options


    data = {
        'goods':goods,
        'goods_specs':goods_specs,
        'sku':sku
    }

    return data
