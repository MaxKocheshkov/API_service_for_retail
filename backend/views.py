from django.contrib.auth import authenticate, login
from django.contrib.auth.password_validation import validate_password

from django.http import JsonResponse, HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import activate
from rest_framework.authtoken.models import Token

from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from transliterate.utils import _

from backend.forms import RegistrationForm, ContactForm, OrderForm, LoginForm
from backend.models import Category, Product, Shop, ProductInfo, Cart, CartItem, Order, User
from backend.serializers import UserSerializer


# class UserView(APIView):
#
#     template_name = "registration.html"
#     """
#         Класс для регистрации и удаления пользователя
#     """
#     # регистрация нового пользователя
#     def post(self, request, *args, **kwargs):
#         errors_dict = {}
#         required_fields = ['password', 'password_repeat', 'email', 'username']
#
#         for field_name in required_fields:
#             # Проверка наличия необходимых аргументов
#             field = request.data.get(field_name)
#             if not field:
#                 errors_dict[field_name] = 'Необходимо заполнить.'
#             else:
#                 # Проверка пароля
#                 if field_name == 'password':
#                     try:
#                         validate_password(request.data['password'])
#                     except Exception as e:
#                         errors_list = []
#                         for error in e:
#                             activate('ru')
#                             errors_list.append(_(error))
#                         errors_dict['password'] = errors_list
#
#                 # Проверка повтора пароля на совпадение с паролем
#                 elif field_name == 'password_repeat':
#                     if request.data['password']:
#                         if not request.data['password'] == request.data['password_repeat']:
#                             errors_dict['password_repeat'] = 'Пароли не совпадают.'
#                     else:
#                         errors_dict['password_repeat'] = 'Сначала придумайте пароль.'
#
#                 # Проверка уникальности логина
#                 elif field_name == 'username':
#                     if User.objects.filter(username=request.data['username']):
#                         errors_dict['username'] = 'Пользоваетль с таким именем уже существует.'
#
#                 # Проверка уникальности email
#                 elif field_name == 'email':
#                     if User.objects.filter(email=request.data['email']):
#                         errors_dict['email'] = 'Пользоваетль с таким email уже существует.'
#
#         # Если словарь с ошибками не пуст, то отправляем его ответ
#         if errors_dict:
#             return JsonResponse({'Status': False, 'Errors': errors_dict})
#
#         # Если ошибок нет, то соханяем пользователя, создаем для него токен авторизации
#
#         serializer = UserSerializer(data=request.data)
#         if serializer.is_valid():
#             # Сохранение пользователя
#             user = serializer.save()
#             user.is_email_sent = True
#             user.set_password(request.data['password'])
#             if 'firstname' in request.data:
#                 user.first_name = request.data['firstname']
#             if 'lastname' in request.data:
#                 user.last_name = request.data['lastname']
#             user.save()
#
#             # Создание токена
#             Token.objects.get_or_create(user=user)
#
#             return JsonResponse({'Status': True})
#         else:
#             return JsonResponse({'Status': False, 'Errors': serializer.errors})

def registration_view(request):
    form = RegistrationForm(request.POST or None)
    context = {}
    context['form'] = form
    if form.is_valid():
        new_user = form.save(commit=False)
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        new_user.set_password(password)
        # new_user.user_name = form.cleaned_data['user_name']
        new_user.email = email
        new_user.company = form.cleaned_data['company']
        new_user.position = form.cleaned_data['position']
        new_user.save()

        login_user = authenticate(email=email, password=password)
        if login_user:
            login(request, login_user)
            return HttpResponseRedirect(reverse('catalog'))
        return HttpResponseRedirect(reverse('catalog'))

    return render(request, 'registration.html', context)


def login_view(request):
    form = LoginForm(request.POST or None)
    context = {}
    context['form'] = form

    if form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        print(password)
        # email = User.objects.get(email=email).email

        login_user = authenticate(email=email, password=password)
        if login_user:
            login(request, login_user)
            return HttpResponseRedirect(reverse('catalog'))

    return render(request, 'login.html', context)


def catalog_view(request, *args, **kwargs):
    category = request.GET.get('category')
    shop = request.GET.get('shop')

    context = {}
    products = Product.objects.all()

    if category:
        products = Product.objects.filter(category__name__iexact=category)

    if shop:
        productinfos = ProductInfo.objects.filter(shop__name__iexact=shop)
        products = []
        for productinfo in productinfos:
            products.append(productinfo.product)

    context["products"] = products
    context['shops'] = Shop.objects.all()
    context['categories'] = Category.objects.all()

    return render(request, 'catalog.html', context)


def product_detail_view(request, *args, **kwargs):
    context = {}
    slug = kwargs['slug']
    product = get_object_or_404(Product, slug=slug)
    context['product'] = product
    context['categories'] = Category.objects.all()

    return render(request, 'product_detail.html', context)


def products_of_category_view(request, *args, **kwargs):
    slug = kwargs['slug']

    context = {}
    context['products'] = Product.objects.filter(category__title__iexact=slug)
    context['categories'] = Category.objects.all()
    return render(request, 'products_of_category.html', context)


# Cart's views

def cart_session(request):
    try:
        cart_id = request.session['cart_id']
        cart = Cart.objects.get(pk=cart_id)
        request.session['total'] = cart.items.count()
    except:
        cart = Cart()
        cart.save()
        cart_id = cart.id
        request.session['cart_id'] = cart_id
        cart = Cart.objects.get(id=cart_id)
    return cart


def cart_view(request):
    context = {}
    context['cart'] = cart_session(request)
    return render(request, 'cart.html', context)


def add_to_cart_view(request):
    productinfopk = request.GET.get('productinfopk')
    productinfo = ProductInfo.objects.get(pk=productinfopk)

    cart = cart_session(request)
    cart.add_to_cart(productinfo)

    cart.count_cart_total()

    return JsonResponse({})


def change_productinfo_view(request):
    productinfopk = request.GET.get('productinfopk')
    cartitempk = request.GET.get('cartitempk')

    productinfo = ProductInfo.objects.get(pk=productinfopk)
    cartitem = CartItem.objects.get(pk=cartitempk)

    cartitem.productinfo = productinfo
    cartitem.save()

    return JsonResponse({})


def remove_from_cart_view(request):
    cartitempk = request.GET.get('cartitempk')
    cart = cart_session(request)
    cart_item = CartItem.objects.get(pk=cartitempk)
    cart.remove_from_cart(cart_item)

    cart_total = cart.count_cart_total()
    return JsonResponse({'cart_total': cart_total,
                         'cartitempk': cartitempk})


def change_item_quantity_view(request):
    context = {}
    cart = cart_session(request)
    context['cart'] = cart
    quantity = request.GET.get('quantity', 1)
    cartitempk = request.GET.get('cartitempk')

    cart_item = CartItem.objects.get(pk=cartitempk)
    cart_item.quantity = quantity
    cart_item.save()

    cart_total = cart.cart_total

    return JsonResponse({'item_total': cart_item.item_total,
                         'cartitempk': cartitempk,
                         'cart_total': cart_total})


def checkout_view(request):
    context = {}
    context['cart'] = cart_session(request)
    context['categories'] = Category.objects.all()
    return render(request, 'checkout.html', context)


def order_create_view(request):
    context = {}
    form = OrderForm(request.POST or None)
    context['form'] = OrderForm(request.POST or None)
    cart = cart_session(request)
    context['cart'] = cart

    if form.is_valid():
        new_order = Order()
        new_order.user = request.user
        new_order.cart = cart
        new_order.first_name = form.cleaned_data['user_name']
        new_order.phone = form.cleaned_data['phone']
        new_order.buying_type = form.cleaned_data['buying_type']
        new_order.address = form.cleaned_data['address']
        new_order.comment = form.cleaned_data['comment']
        new_order.total = cart.cart_total
        new_order.save()

        del request.session['cart_id']
        return HttpResponseRedirect(reverse('congratulations'))
    return render(request, 'order.html', context)


def congratulations_view(request):
    context = {}
    user = request.user
    try:
        context['order'] = Order.objects.filter(user=user).latest('create_date')
    except:
        context['order'] = None
    return render(request, 'congratulations.html', context)


# Account's views

def account_view(request):
    context = {}
    try:
        context['orders'] = Order.objects.filter(user=request.user).order_by('-pk')
    except:
        context['orders'] = None
    context['categories'] = Category.objects.all()
    context['contact_form'] = ContactForm()
    return render(request, 'account.html', context)


def account_order_view(request, id, *args, **kwargs):
    order = get_object_or_404(Order, pk=id)
    context = {}
    if request.user == order.user:
        context['order'] = order
    else:
        raise Http404
    return render(request, 'account_order.html', context)
