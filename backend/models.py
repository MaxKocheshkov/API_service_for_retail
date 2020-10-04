from decimal import Decimal

from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import AbstractUser, PermissionsMixin, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.db.models.signals import pre_save
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_rest_passwordreset.tokens import get_token_generator
from django.utils.text import slugify
from transliterate import translit

from django.conf import settings


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), unique=True)
    username_validator = UnicodeUsernameValidator()
    user_name = models.CharField(_('user name'), max_length=150,
                                 help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
                                 validators=[username_validator],
                                 error_messages={
                                     'unique': _("A user with that username already exists."),
                                 }, default='Введите имя',
                                 )
    company = models.CharField(_('company'), max_length=100, blank=True)
    position = models.CharField(_('position'), max_length=100, blank=True)
    date_joined = models.DateTimeField(_('date joined'), auto_now_add=True)
    is_staff = True

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return f'{self.email} - {self.get_name()}'

    def get_full_name(self):
        return f'{self.first_name} {self.second_name} {self.last_name}'

    get_full_name.short_description = "Full name of the person"

    def get_name(self):
        return f'{self.first_name} {self.last_name}'


CONTACT_TYPE_CHOICES = (
    ('Телефон', 'Телефон'),
    ('Адрес', 'Адрес'),
)


class Contact(models.Model):  # ?
    type = models.CharField(max_length=100, choices=CONTACT_TYPE_CHOICES, default='Телефон')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    value = models.CharField(max_length=200, null=True)

    def __str__(self):
        return f'{self.pk}'


def pre_save_slug(sender, instance, *args, **kwargs):
    if not instance.slug:
        try:
            instance.slug = slugify(translit(instance.name, reversed=True))
        except:
            instance.slug = slugify(instance.name)


SHOP_STATE_CHOICES = (
    ('on', 'on'),
    ('off', 'off')
)


class Shop(models.Model):
    name = models.CharField(max_length=90)
    url = models.CharField(max_length=120, blank=True, null=True)
    logo = models.ImageField(blank=True)
    state = models.CharField(max_length=3, choices=SHOP_STATE_CHOICES, default='off')
    user_admins = models.ManyToManyField('User', related_name='controlled_shop')
    filename = models.FileField(upload_to='data/', null=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=30)
    shops = models.ManyToManyField('Shop', related_name='categories')
    slug = models.SlugField(blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category', kwargs={'slug': self.slug})


pre_save.connect(pre_save_slug, sender=Category)


class Product(models.Model):
    name = models.CharField(max_length=120)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    model = models.CharField(max_length=120, blank=True)
    slug = models.SlugField(blank=True)
    image = models.ImageField(blank=True)
    description = models.TextField(null=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product', kwargs={'slug': self.slug})


pre_save.connect(pre_save_slug, sender=Product)


class ProductInfo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    quantity = models.PositiveSmallIntegerField()
    price = models.DecimalField(max_digits=9, decimal_places=2, default=0.00)

    def __str__(self):
        return f'{self.product.name} - Product Info'


class Parameter(models.Model):
    name = models.CharField(max_length=120)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    value = models.CharField(max_length=90)

    def __str__(self):
        return f'{self.product_info.product.name} - {self.parameter}'


def pre_save_cart_item_total(sender, instance, *args, **kwargs):
    # Автоматически считают сумму стоимости предметов элемента корзины перед сохранением этого элемента.
    instance.item_total = instance.productinfo.price * instance.quantity


class CartItem(models.Model):
    productinfo = models.ForeignKey(ProductInfo, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    item_total = models.DecimalField(max_digits=9, decimal_places=2, default=0.00, blank=True)

    def __str__(self):
        return f'Cart item №{self.pk}'


pre_save.connect(pre_save_cart_item_total, sender=CartItem)


def pre_save_total(sender, instance, *args, **kwargs):
    # Автоматически считают сумму стоимости предметов корзины перед сохранением корзины.
    total = Decimal(0)
    for item in instance.items.all():
        total += item.item_total
    instance.cart_total = total


class Cart(models.Model):
    items = models.ManyToManyField(CartItem)
    cart_total = models.DecimalField(max_digits=9, decimal_places=2, default=0.00, blank=True)

    def __str__(self):
        return f'Cart №{self.pk}'

    def add_to_cart(self, productinfo):
        # Добавляет productInfo к корзине, задает ей кол-во == 1
        cart = self
        new_item, _ = CartItem.objects.get_or_create(productinfo=productinfo)

        if new_item not in cart.items.all():
            new_item.quantity = 1
            new_item.save()
            cart.items.add(new_item)
            cart.save()

    def remove_from_cart(self, cartitem):
        cart = self
        for cart_item in cart.items.all():
            if cart_item == cartitem:
                cart.items.remove(cart_item)
                cart.save()


pre_save.connect(pre_save_total, sender=Cart)

ORDER_STATUS_CHOICES = (
    ('Новый', 'Новый'),
    ('Подтвержден', 'Подтвержден'),
    ('Собран', 'Собран'),
    ('Отправлен', 'Отправлен'),
    ('Доставлен', 'Доставлен'),
    ('Отменен', 'Отменен'),
)


class Order(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='orders', blank=True,
                             on_delete=models.CASCADE, null=True)
    user_name = models.CharField(max_length=100, null=True)
    phone = models.CharField(default=None, max_length=20, verbose_name='Телефон')
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, null=True)
    buying_type = models.CharField(max_length=40, choices=(('Самовывоз', 'Самовывоз'), ('Доставка', 'Доставка')),
                                   default='Самовывоз')
    address = models.CharField(max_length=500, default='Самовывоз', blank=True)
    comment = models.TextField(blank=True)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=100, choices=ORDER_STATUS_CHOICES, default='Новый')

    def __str__(self):
        return f'Заказ №{self.pk}'
