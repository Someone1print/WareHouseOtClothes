"""Permission helpers for role-based access control.

Все роли определены в [warehouse.models.Position]. Суперпользователь Django
автоматически имеет полный доступ — это нужно для первого входа до того,
как директор раздаст аккаунты сотрудникам.
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .models import Position


def get_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return Position.ROLE_DIRECTOR
    profile = getattr(user, 'profile', None)
    if not profile:
        return None
    return profile.role


def get_employee(user):
    """Возвращает Employee текущего пользователя (или None для суперюзера без профиля)."""
    if not user.is_authenticated:
        return None
    profile = getattr(user, 'profile', None)
    return profile.employee if profile else None


def is_director(user):
    return get_role(user) == Position.ROLE_DIRECTOR


def has_role(user, *roles):
    role = get_role(user)
    if role is None:
        return False
    if role == Position.ROLE_DIRECTOR:
        return True
    return role in roles


def role_required(*allowed_roles):
    """Декоратор: только пользователи с одной из ролей (директор всегда проходит)."""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if has_role(request.user, *allowed_roles):
                return view_func(request, *args, **kwargs)
            messages.error(request, "У вас нет прав на это действие.")
            return redirect('index')
        return _wrapped
    return decorator


def director_required(view_func):
    """Декоратор: только директор / суперюзер."""
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if is_director(request.user):
            return view_func(request, *args, **kwargs)
        messages.error(request, "Только для директора.")
        return redirect('index')
    return _wrapped
