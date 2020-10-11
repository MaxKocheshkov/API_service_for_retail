import yaml
from requests import get

from django.core.validators import URLValidator
from django.core.management.base import BaseCommand

from backend.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, url, *args, **options):
        validate_url = URLValidator()
        validate_url(url)
        stream = get(url).content

        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            return {'Status': False, 'Errors': str(e)}
        else:
            try:
                shop, _ = Shop.objects.get_or_create(name=data['shop'])
            except Shop.DoesNotExist:
                return {'Status': 'Error', "Error": "Магазина не существует. Обратитесь к администратору сайта"}

            for category in data['categories']:
                category_object, _ = Category.objects.get_or_create(id=category['id'],
                                                                    name=category['name'])
                category_object.shops.add(shop.id)
                category_object.save()

            product_info_object_list = []
            for item in data['goods']:
                product, _ = Product.objects.get_or_create(pk=item['id'],
                                                           name=item['name'],
                                                           category_id=item['category'],
                                                           model=item['model'])

                product_info, is_product_info_created = ProductInfo.objects.get_or_create(product_id=product.id,
                                                                                          shop_id=shop.id,
                                                                                          defaults={
                                                                                              'price': item['price'],
                                                                                              'quantity': item[
                                                                                                  'quantity']})

                if not is_product_info_created:
                    product_info.price = item['price']
                    product_info.quantity = item['quantity']
                    product_info_object_list.append(product_info)

                product_parameter_object_list = []
                for name, value in item['parameters'].items():
                    parameter_object, _ = Parameter.objects.get_or_create(name=name)

                    product_parameter_object, is_product_parameter_created = ProductParameter.objects.get_or_create(
                        product_info_id=product_info.id,
                        parameter_id=parameter_object.id,
                        defaults={'value': value}
                    )

                    if not is_product_parameter_created:
                        product_parameter_object.value = value
                        product_parameter_object_list.append(product_parameter_object)

                ProductParameter.objects.bulk_update(product_parameter_object_list, ['value'])
            ProductInfo.objects.bulk_update(product_info_object_list, ['price', 'quantity'])

            return {'Status': 'Success'}
