# Верстальщик
from rest_framework import serializers
from backend.models import User, Contact, Product, Category, ProductParameter, ProductInfo, Shop, CartItem, Order, \
    OrderItem, Cart


class ShopSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField('get_email')

    def get_email(self, obj):
        return obj.user.email

    class Meta:
        model = Shop
        fields = ('id', 'user', 'name', 'url', 'email')


class UserSerializer(serializers.ModelSerializer):
    shop = ShopSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'company', 'position', 'type', 'shop')


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ('id', 'user', 'city', 'street', 'house',
                  'structure', 'building', 'apartment', 'phone')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name')


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ('name', 'category', 'on_sale')


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ('id', 'parameter', 'value',)
        read_only_fields = ('id',)


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)
    shop = ShopSerializer(read_only=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'external_id', 'model', 'product', 'shop',
                  'quantity', 'price', 'price_rrc', 'image', 'product_parameters',)
        read_only_fields = ('id',)


class CartItemSerializer(serializers.ModelSerializer):
    product_info = ProductInfoSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ('id', 'product_info', 'quantity',)
        read_only_fields = ('id',)


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(read_only=True, many=True)

    class Meta:
        model = Cart
        fields = ('id', 'items', )
        read_only_fields = ('id',)


class OrderItemSerializer(serializers.ModelSerializer):
    product_info = ProductInfoSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product_info', 'quantity')
        read_only_fields = ('id',)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    contact = ContactSerializer(read_only=True)
    shop = ShopSerializer(read_only=True)
    state = serializers.CharField(source='get_state_display')
    user = UserSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'user', 'dt', 'state', 'contact',
                  'shop', 'items', 'total_summ')
        read_only_fields = ('id',)

    def get_state(self, obj):
        return obj.get_state_display()