"""Authentication: login / logout / account management."""
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render, get_object_or_404

from .models import Employee, UserProfile
from .permissions import director_required


class LoginForm(forms.Form):
    username = forms.CharField(label="Логин", max_length=150)
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user is None:
                messages.error(request, "Неверный логин или пароль.")
            else:
                login(request, user)
                return redirect('index')
    else:
        form = LoginForm()
    return render(request, 'warehouse/auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "Вы вышли из системы.")
    return redirect('login')


class AccountCreateForm(forms.Form):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.none(),
        label="Сотрудник",
        empty_label="— выберите сотрудника —",
    )
    username = forms.CharField(label="Логин", max_length=150)
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput, min_length=4)
    password2 = forms.CharField(label="Повторите пароль", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Только сотрудники без аккаунтов
        self.fields['employee'].queryset = Employee.objects.filter(account__isnull=True)

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким логином уже существует.")
        return username

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password2'):
            raise forms.ValidationError("Пароли не совпадают.")
        return cleaned


@director_required
def account_list(request):
    accounts = UserProfile.objects.select_related('user', 'employee', 'employee__position').all()
    return render(request, 'warehouse/auth/account_list.html', {'accounts': accounts})


@director_required
def account_create(request):
    if request.method == 'POST':
        form = AccountCreateForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            UserProfile.objects.create(
                user=user,
                employee=form.cleaned_data['employee'],
            )
            messages.success(request, f"Аккаунт «{user.username}» создан.")
            return redirect('account_list')
    else:
        form = AccountCreateForm()
    return render(request, 'warehouse/auth/account_form.html', {
        'form': form,
        'title': 'Создать аккаунт сотрудника',
    })


@director_required
def account_delete(request, pk):
    profile = get_object_or_404(UserProfile, pk=pk)
    if request.method == 'POST':
        username = profile.user.username
        profile.user.delete()  # каскадно удалит profile
        messages.success(request, f"Аккаунт «{username}» удалён.")
        return redirect('account_list')
    return render(request, 'warehouse/auth/account_confirm_delete.html', {'profile': profile})
