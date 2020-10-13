from django.urls import path
from django_rest_passwordreset.views import reset_password_request_token, reset_password_confirm

from backend.views import UserView, LogIn, AccountInfo, ConfirmEmail, AccountContacts,\
    CategoryViewSet, ProductView, PartnerView, PartnerInfo, ParthnerProducts, UserCart, OrderView

app_name = 'backend'
urlpatterns = [
    path('registration/', UserView.as_view()),
    path('login/', LogIn.as_view()),
    path('info/', AccountInfo.as_view()),
    path('contact/', AccountContacts.as_view()),
    path('products/', ProductView.as_view()),
    path('partner/', PartnerView.as_view()),
    path('partner_info/', PartnerInfo.as_view()),
    path('partner_products/', ParthnerProducts.as_view()),
    path('cart/', UserCart.as_view()),
    path('order/', OrderView.as_view()),
    path('verify/', ConfirmEmail.as_view()),
]
