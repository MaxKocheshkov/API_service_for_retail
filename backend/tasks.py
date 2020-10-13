import logging
from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings


@shared_task
def send_email(title, body, to, files_path=None):
    email = EmailMessage(
        title,
        body,
        f'Магазин <{settings.EMAIL_HOST_USER}>',
        to
    )

    if files_path:
        for file_path in files_path:
            email.attach_file(file_path)

    email.send()


@shared_task
def do_import(data, shop_id):
    from .models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter

    shop = Shop.objects.get(id=shop_id)
   # Добавление категорий
    if data.get('categories'):
        for category in data.get('categories'):
            category_id = category.get('id')
            if category_id:
                category_object, _ = Category.objects.get_or_create(
                    name=category.get('name'), id=category.get('id'))
            else:
                category_object, _ = Category.objects.get_or_create(
                    name=category.get('name'))

    # Добавление товаров
    for item in data.get('goods'):
        category, _ = Category.objects.get_or_create(
            name=item.get('category'))
        category.shops.add(shop)
        category.save()

        try:
            external_id = item.get('id')
            product = Product.objects.get(
                product_infos__external_id=external_id, product_infos__shop=shop)
            product.name = item.get('name')
            product.category = category
            product.save()

        except Product.DoesNotExist:
            product = Product.objects.create(
                name=item.get('name'), category=category)

        try:
            product_info = ProductInfo.objects.get(product=product)
            product_info.external_id = item.get('id')
            product_info.model = item.get('model')
            product_info.price = item.get('price')
            product_info.price_rrc = item.get('price_rrc')
            product_info.quantity = item.get('quantity')
            product_info.shop = shop
            product_info.save()

        except ProductInfo.DoesNotExist:
            product_info = ProductInfo.objects.create(product_id=product.id,
                                                      external_id=item['id'],
                                                      model=item['model'],
                                                      price=item['price'],
                                                      price_rrc=item['price_rrc'],
                                                      quantity=item['quantity'],
                                                      shop_id=shop.id)

        for name, value in item['parameters'].items():
            parameter_object, _ = Parameter.objects.get_or_create(
                name=name)
            product_parameter, _ = ProductParameter.objects.get_or_create(product_info_id=product_info.id,
                                                                          parameter_id=parameter_object.id)
            product_parameter.value = value
            product_parameter.save()
