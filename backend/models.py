from django.db import models
from django.contrib.auth.models import AbstractUser
from django_rest_passwordreset.tokens import get_token_generator
from django.db.models import signals
from .tasks import send_email
from django.urls import reverse
import uuid

STATE_CHOICES = (
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
)

USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),
)


class User(AbstractUser):
    type = models.CharField(verbose_name='Тип пользователя',
                            choices=USER_TYPE_CHOICES, max_length=5, default='buyer')
    company = models.CharField(
        verbose_name='Компания', max_length=40, blank=True)
    position = models.CharField(
        verbose_name='Должность', max_length=40, blank=True)
    is_active = models.BooleanField(default=False)
    is_email_sent = models.BooleanField(default=False)
    verification_uuid = models.UUIDField(
        'Уникальный код подтверждения', default=uuid.uuid4)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


def user_post_save(sender, instance, signal, *args, **kwargs):
    if not instance.is_active and not instance.is_email_sent:
        send_email.delay(
            'Подтверждение почты',
            'Спасибо за регистрцию на нашем сайте!\n\n'
            'Перейдите по ссылке чтобы активировать аккаунт: '
            f'http://localhost:3000/verify/{str(instance.verification_uuid)}',
            [instance.email],
        )


signals.post_save.connect(user_post_save, sender=User)


class ConformaionCode(models.Model):
    @staticmethod
    def generate_code():
        return get_token_generator().generate_token()

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    code = models.CharField(max_length=100)

    def set(self):
        self.code = self.generate_code()

    def __str__(self):
        return f'Код подтверждения для ${self.user}'


class Contact(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='contacts', blank=True, null=True,
                             on_delete=models.CASCADE)

    city = models.CharField(max_length=50, verbose_name='Город', blank=True, null=True)
    street = models.CharField(max_length=100, verbose_name='Улица', blank=True, null=True)
    house = models.CharField(max_length=15, verbose_name='Дом', blank=True, null=True)
    structure = models.CharField(
        max_length=15, verbose_name='Корпус', blank=True, null=True)
    building = models.CharField(
        max_length=15, verbose_name='Строение', blank=True, null=True)
    apartment = models.CharField(
        max_length=15, verbose_name='Квартира', blank=True, null=True)
    phone = models.CharField(max_length=20, verbose_name='Телефон', blank=True, null=True)

    class Meta:
        verbose_name = 'Контакты пользователя'
        verbose_name_plural = "Список контактов пользователя"

    def __str__(self):
        return f'{self.city} {self.street} {self.house}'


class Shop(models.Model):
    name = models.CharField(max_length=50, verbose_name='Название', blank=True, null=True)
    url = models.URLField(verbose_name='Ссылка', null=True, blank=True)
    user = models.OneToOneField(User, verbose_name='Пользователь',
                                blank=True, null=True,
                                on_delete=models.CASCADE)
    state = models.BooleanField(
        verbose_name='статус получения заказов', default=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = "Список магазинов"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(
        max_length=40, verbose_name='Название', default='Неизвестная категория')
    shops = models.ManyToManyField(
        Shop, verbose_name='Магазины', related_name='categories', blank=True, null=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = "Список категорий"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=80, verbose_name='Название')
    category = models.ForeignKey(Category, verbose_name='Категория', related_name='products', blank=True, null=True,
                                 on_delete=models.CASCADE)
    on_sale = models.BooleanField(verbose_name='На продаже', default=True)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = "Список продуктов"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    model = models.CharField(max_length=80, verbose_name='Модель', blank=True)
    external_id = models.PositiveIntegerField(verbose_name='Внешний ИД', blank=True, null=True)
    product = models.ForeignKey(Product, verbose_name='Продукт', related_name='product_infos', blank=True,
                                on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, verbose_name='Магазин', related_name='product_infos', blank=True,
                             on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.PositiveIntegerField(verbose_name='Цена')
    price_rrc = models.PositiveIntegerField(
        verbose_name='Рекомендуемая розничная цена', blank=True, null=True)
    image = models.ImageField(
        verbose_name='Изображение', null=True, blank=True)

    class Meta:
        verbose_name = 'Информация о продукте'
        verbose_name_plural = "Информационный список о продуктах"

    def __str__(self):
        return self.product.name

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related('product')


class Parameter(models.Model):
    name = models.CharField(max_length=40, verbose_name='Название')

    class Meta:
        verbose_name = 'Имя параметра'
        verbose_name_plural = "Список имен параметров"
        ordering = ('-name',)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте',
                                     related_name='product_parameters', blank=True, null=True,
                                     on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, verbose_name='Параметр', related_name='product_parameters', blank=True,
                                  on_delete=models.CASCADE)
    value = models.CharField(verbose_name='Значение', max_length=100)

    class Meta:
        verbose_name = 'Параметр'
        verbose_name_plural = "Список параметров"


class Order(models.Model):
    STATE_CHOICES = (
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('assembled', 'Собран'),
        ('sent', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('canceled', 'Отменен'),
    )
    external_id = models.PositiveIntegerField(
        verbose_name='Дополнительный ID', blank=True, null=True)
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='orders', blank=True, null=True,
                             on_delete=models.SET_NULL)
    dt = models.DateTimeField(auto_now_add=True)
    state = models.CharField(
        verbose_name='Статус', choices=STATE_CHOICES, max_length=15, default='new')
    contact = models.ForeignKey(Contact, verbose_name='Контакт',
                                blank=True, null=True,
                                on_delete=models.SET_NULL)
    shop = models.ForeignKey(Shop, verbose_name='Магазин',
                             null=True, blank=True, on_delete=models.SET_NULL)
    items = models.ManyToManyField('OrderItem', related_name='ordered_items')
    total_summ = models.PositiveIntegerField(verbose_name='Cумма', default=0)
    order_pdf = models.FilePathField(
        verbose_name='Заказ в PDF', null=True, blank=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = "Список заказ"
        ordering = ('-dt',)

    def __str__(self):
        return f'Заказ №{self.id}, магазин {self.shop.name}'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related('shop')


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='ordered_items', blank=True,
                              on_delete=models.CASCADE)

    product_info = models.ForeignKey(ProductInfo, verbose_name='Информация о продукте', related_name='ordered_items',
                                     blank=True, null=True,
                                     on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = "Список заказанных позиций"


class Cart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь')
    items = models.ManyToManyField(
        'CartItem', related_name='cart_items', blank=True)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return f'Корзина {self.user}'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE,
                             related_name='cart_items', blank=True, null=True)
    product_info = models.ForeignKey(
        ProductInfo, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.IntegerField(verbose_name='Количество', default=0)

    def __str__(self):
        return f'{self.product_info.product} ({self.quantity}шт.)'

    class Meta:
        verbose_name_plural = 'Список товаров корзины'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related('product_info', 'product_info__product')