from .permissions import get_role, get_employee, is_director
from .models import Position


def auth_context(request):
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {
            'current_role': None,
            'current_employee': None,
            'is_director': False,
            'can_warehouse': False,
            'can_production': False,
            'can_sales': False,
            'can_accountant': False,
        }
    role = get_role(user)
    director = is_director(user)
    return {
        'current_role': role,
        'current_employee': get_employee(user),
        'is_director': director,
        'can_warehouse': director or role == Position.ROLE_WAREHOUSE,
        'can_production': director or role == Position.ROLE_PRODUCTION,
        'can_sales': director or role == Position.ROLE_SALES,
        'can_accountant': director or role == Position.ROLE_ACCOUNTANT,
    }
