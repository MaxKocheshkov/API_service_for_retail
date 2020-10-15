from django.test import TestCase, Client, override_settings, modify_settings
from backend.models import User, Contact, Shop, ProductInfo, Category, Order
from django.contrib import auth
import json
from urllib.parse import urlencode
from rest_framework.authtoken.models import Token
from django.http import QueryDict
from orders import settings
from rest_framework.test import APIClient
import yaml
import os
from requests import get

CLIENT = APIClient()
FIXTURES = 'backend/test_data/fixtures.json'


class SignUpTestCase(TestCase):
    def test_signup(self):
        response = CLIENT.post(
            '/api/registration/',
            {
                'username': 'test',
                'email': 'test@test.com',
                'password': '12345Test',
                'password_repeat': '12345Test'
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], True)

    def test_invalid_signup(self):
        response = CLIENT.post(
            '/api/registration/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['Status'], False)

        self.assertEqual(
            response.json()['Errors'].__contains__('password'), True)
        self.assertEqual(response.json()['Errors'].__contains__(
            'password_repeat'), True)
        self.assertEqual(response.json()['Errors'].__contains__('email'), True)
        self.assertEqual(
            response.json()['Errors'].__contains__('username'), True)


class AuthTestCase(TestCase):
    fixtures = [FIXTURES]

    def setUp(self):
        self.new_user = User.objects.get(username='test_not_active_user')

        self.buyer_token = Token.objects.select_related(
            'user').get(user__username='test_buyer')

    def test_confirm_user(self):
        response = CLIENT.post('/api/confirmation/',
                               {'uuid': self.new_user.verification_uuid})

        self.new_user.refresh_from_db()
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(self.new_user.is_active, True)

    def test_login(self):
        response = CLIENT.post(
            '/api/login/', {'username': self.buyer_token.user.username, 'password': 123456})

        data = response.json()
        self.assertEqual(data['Status'], True)
        self.assertEqual(data['Info']['token'], self.buyer_token.key)


class AccountInfoTestCase(TestCase):
    fixtures = [FIXTURES]

    def setUp(self):
        self.token = Token.objects.select_related(
            'user').get(user__username='test_buyer')

    def test_get_account_info(self):
        response = CLIENT.get(
            '/api/info/', HTTP_AUTHORIZATION=f'Token {self.token.key}')

        data = response.json()
        self.assertEqual(data['Status'], True)
        self.assertEqual(data['Info']['username'], self.token.user.username)
        self.assertEqual(data['Info']['email'], self.token.user.email)
        self.assertEqual(data['Info']['type'], self.token.user.type)

    def test_change_account_info(self):
        response = CLIENT.put(
            '/api/info/',
            {'first_name': 'Test Name', 'last_name': 'Test Surname'},
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )

        self.token.refresh_from_db()
        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(self.token.user.first_name, 'Test Name')
        self.assertEqual(self.token.user.last_name, 'Test Surname')


class ContactTestCase(TestCase):
    fixtures = [FIXTURES]

    def setUp(self):
        self.token = Token.objects.select_related(
            'user').get(user__username='test_buyer')

    def test_get_contacts(self):
        response = CLIENT.get(
            '/api/contact/', HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = response.json()
        self.assertEqual(data['Status'], True)
        self.assertEqual(type(data['Info']), list)

    def test_create_contact(self):
        response = CLIENT.post(
            '/api/contact/',
            {'city': 'Moscow', 'street': 'Volkova',
             'house': '1', 'phone': '+71111111111'},
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )

        data = response.json()
        self.assertEqual(data['Status'], True)
        self.assertEqual(data['Info']['user'], self.token.user.id)

    def test_change_contact(self):
        response = CLIENT.put(
            '/api/contact/',
            {'id': '1', 'city': 'Moscow'},
            HTTP_AUTHORIZATION=f'Token {self.token.key}')

        data = response.json()

        self.assertEqual(data['Status'], True)
        self.assertEqual(data['Info']['city'], 'Moscow')

    def test_delete_contact(self):
        del_response = CLIENT.delete(
            '/api/contact/',
            {'id': '1'},
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        self.assertEqual(del_response.json()['Status'], True)

        get_response = CLIENT.get(
            '/api/contact/', HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.assertEqual(len(get_response.json()['Info']), 0)


class ShopTestCase(TestCase):
    fixtures = [FIXTURES]

    def setUp(self):
        self.seller_token = Token.objects.select_related(
            'user').get(user__username='test_seller')
        self.buyer_token = Token.objects.select_related(
            'user').get(user__username='test_buyer')
        self.shop = Shop.objects.get(user=self.seller_token.user)

    def test_register_and_delete_shop(self):
        response = CLIENT.post(
            '/api/partner/',
            {'agreement': True, 'name': 'Buyer Shop'},
            HTTP_AUTHORIZATION=f'Token {self.buyer_token.key}'
        )

        self.buyer_token.refresh_from_db()
        self.assertEqual(self.buyer_token.user.type, 'shop')

        response = CLIENT.delete(
            '/api/partner/',
            HTTP_AUTHORIZATION=f'Token {self.buyer_token.key}'
        )

        self.buyer_token.refresh_from_db()
        self.assertEqual(self.buyer_token.user.type, 'buyer')

    def test_get_shop_info_owner(self):
        response = CLIENT.post(
            '/api/partner_info/',
            HTTP_AUTHORIZATION=f'Token {self.seller_token.key}'
        )

        data = response.json()
        self.assertEqual(data['Status'], True)
        self.assertEqual(data['Info']['user'], self.seller_token.user.id)

    def test_get_shop_info_ID(self):
        response = CLIENT.post(
            '/api/partner_info/',
            {'id': 1}
        )

        data = response.json()
        self.assertEqual(data['Status'], True)
        self.assertEqual(data['Info']['user'], self.seller_token.user.id)

    def test_change_shop_info(self):
        self.assertEqual(self.shop.name, "Test Seller's shop")

        response = CLIENT.put(
            '/api/partner_info/',
            {'name': 'Shop'},
            HTTP_AUTHORIZATION=f'Token {self.seller_token.key}'
        )

        self.assertEqual(response.json()['Status'], True)
        self.shop.refresh_from_db()
        self.assertEqual(self.shop.name, 'Shop')


class ProductTestCase(TestCase):
    fixtures = [FIXTURES]

    def setUp(self):
        self.token = Token.objects.get(user__username='test_seller')
        self.product = ProductInfo.objects.select_related(
            'product', 'product__category').get(product__name='Test product')

    def test_add_product_text(self):
        data = {
            'goods': [
                {
                    'id': 1284469,
                    'category': 'Телевизоры',
                    'model': 'DEXP M22D7200E',
                    'name': '32" (85 см) Телевизор LED DEXP M22D7200E черный',
                    'price': 9500,
                    'price_rrc': 10499,
                    'quantity': 22,
                    'parameters': {
                        "Диагональ (дюйм)": 32,
                        "Разрешение (пикс)": '1920х1080',
                        "Тип экрана": 'Direct LED',
                        "Формат экрана": '16:9'
                    }
                }
            ]
        }

        yaml_data = yaml.dump(data)
        response = CLIENT.post(
            '/api/partner_products/',
            {'yaml': yaml_data},
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )

        self.assertEqual(response.json()['Status'], True)

    def test_add_product_file(self):
        with open('backend/test_data/yamlExample.yaml', 'r', encoding='utf-8') as file:
            response = CLIENT.post(
                '/api/partner_products/',
                {'file': file},
                HTTP_AUTHORIZATION=f'Token {self.token.key}'
            )
        self.assertEqual(response.json()['Status'], True)

    @override_settings(CELERY_ALWAYS_EAGER=True,
                       CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       BROKER_BACKEND='memory')
    def test_change_product(self):
        data = {
            'goods': [
                {
                    'id': 123,
                    'category': self.product.product.category.name,
                    'model': self.product.model,
                    'name': 'Test product changed',
                    'price': self.product.price,
                    'price_rrc': self.product.price_rrc,
                    'quantity': self.product.quantity,
                    'parameters': {}
                }
            ]
        }

        yaml_data = yaml.dump(data)
        response = CLIENT.post(
            '/api/partner_products/',
            {'yaml': yaml_data},
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )

        self.assertEqual(response.json()['Status'], True)
        self.product.refresh_from_db()
        self.assertEqual(self.product.product.name, 'Test product changed')

    def test_delete_product(self):
        response = CLIENT.delete(
            '/api/partner_products/',
            {'id': 123},
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )

        self.assertEqual(response.json()['Status'], True)
        self.assertEqual(len(ProductInfo.objects.all()), 0)

    def test_get_product(self):
        pass


class CategoryTestCase(TestCase):
    fixtures = [FIXTURES]

    def test_get_category_all(self):
        response = CLIENT.get(
            '/api/categories/',
        )

        data = response.json()
        self.assertEqual(data['Status'], True)
        self.assertEqual(len(data['Info']), 2)

    def test_get_category_shop_id(self):
        response = CLIENT.get(
            '/api/categories/1/',
        )

        data = response.json()
        self.assertEqual(data['Status'], True)
        self.assertEqual(len(data['Info']), 1)
        self.assertEqual(data['Info'][0]['name'], 'test')


class CartTestCase(TestCase):
    fixtures = [FIXTURES]

    def setUp(self):
        self.token = Token.objects.get(user__username='test_buyer')

    def test_get_cart(self):
        response = CLIENT.get(
            '/api/cart/',
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )

        data = response.json()
        self.assertEqual(data['Status'], True)
        self.assertEqual(data['Info']['cart']['items'][0]['quantity'], 1)

    def test_add_to_cart_plus_one(self):
        response = CLIENT.post(
            '/api/cart/',
            {
                'id': 1,
                'operator': '+'
            },
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        data = response.json()
        self.assertEqual(data['Status'], True)
        self.assertEqual(data['Info']['quantity'], 2)

    def test_add_to_cart_minus_one(self):
        response = CLIENT.post(
            '/api/cart/',
            {
                'id': 1,
                'operator': '-'
            },
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        data = response.json()
        self.assertEqual(data['Status'], True)
        self.assertEqual(data['Info']['quantity'], 0)

    def test_add_to_cart_change_count(self):
        response = CLIENT.post(
            '/api/cart/',
            {
                'id': 1,
                'count': 9
            },
            HTTP_AUTHORIZATION=f'Token {self.token.key}'
        )
        data = response.json()
        self.assertEqual(data['Status'], True)
        self.assertEqual(data['Info']['quantity'], 9)


class OrderTestCase(TestCase):
    fixtures = [FIXTURES]

    def setUp(self):
        self.seller_token = Token.objects.get(user__username='test_seller')
        self.buyer_token = Token.objects.get(user__username='test_buyer')

    def test_get_orders(self):
        response = CLIENT.get(
            '/api/order/',
            HTTP_AUTHORIZATION=f'Token {self.seller_token.key}'
        )
        data = response.json()
        self.assertEqual(data['Status'], True)
        self.assertEqual(len(data['Info']['user']), 0)
        self.assertEqual(len(data['Info']['shop']), 1)
        self.assertEqual(data['Info']['shop'][0]['state'], 'Новый')

    def test_change_order_state(self):
        response = CLIENT.put(
            '/api/order/',
            {'id': 1, 'state': 'confirmed'},
            HTTP_AUTHORIZATION=f'Token {self.seller_token.key}'
        )

        self.assertEqual(response.json()['Status'], True)

    def test_create_order(self):
        response = CLIENT.post(
            '/api/order/',
            {'contact': 1},
            HTTP_AUTHORIZATION=f'Token {self.buyer_token.key}'
        )

        data = response.json()
        self.assertEqual(data['Status'], True)
