from django import forms
from backend.models import User, Order, Contact


class ContactForm(forms.ModelForm):
    class Meta(object):
        model = Contact
        fields = (
            'user',
            'city',
            'street',
            'house',
            'structure',
            'building',
            'apartment',
            'phone',
        )


class RegistrationForm(forms.ModelForm):
    password_check = forms.CharField(widget=forms.PasswordInput)
    password_check.label = 'Повторите пароль:'

    password = forms.CharField(widget=forms.PasswordInput)
    password.label = 'Пароль:'
    password.help_text = 'Придумайте пароль.'

    class Meta:
        model = User
        fields = (
            'email',
            'password',
            'password_check',
            'company',
            'position',
        )

        labels = {
            'user_name': 'Имя:',
            'email': 'Email:',
            'username': 'Логин:',
            'company': 'Компания:',
            'position': 'Должность:',
            'type': 'Тип аккаунта:'
        }

        help_texts = {
            'email': 'Пожалуйста, укзаывайте реальный адресс.',
        }

    def clean(self):
        password = self.cleaned_data['password']
        password_check = self.cleaned_data['password_check']
        email = self.cleaned_data['email']

        if password != password_check:
            raise forms.ValidationError('Пароли не совпадают! Попробуйте снова!')

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Этот Email уже занят другим пользователем!')


class LoginForm(forms.Form):
    email = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    email.label = 'Email:'
    password.label = 'Пароль:'

    def clean(self):
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']

        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('Такого Email нет в системе!')

        user = User.objects.get(email=email)
        if user and not user.check_password(password):
            raise forms.ValidationError('Неверный пароль!')


class OrderForm(forms.ModelForm):
    class Meta(object):
        model = Order
        fields = (
            'user',
            'state',
            'contact',
            'shop',
            'total_sum'
        )

        labels = {
            'user': 'Ваше имя: ',
            'state': 'Статус: ',
            'contact': 'Контакт:',
            'shop': 'Магазин:',
            'total_sum': 'Cумма:',
        }

        help_texts = {
            'user': 'Имя по умолчанию взято из вашего профиля.',
        }


class ShopsCheckboxForm(forms.ModelForm):
    shop = forms.DateField(widget=forms.Select(choices=()))

