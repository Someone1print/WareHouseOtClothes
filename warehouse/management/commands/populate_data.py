from django.core.management.base import BaseCommand
from warehouse.models import Unit, Position, Employee, RawMaterial, FinishedProduct, Ingredient, Budget

class Command(BaseCommand):
    help = 'Populates the database with initial data'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # Units
        u_pcs, _ = Unit.objects.get_or_create(name='шт')
        u_m, _ = Unit.objects.get_or_create(name='м')
        u_kg, _ = Unit.objects.get_or_create(name='кг')
        u_roll, _ = Unit.objects.get_or_create(name='катушка')

        # Positions
        pos_store, _ = Position.objects.get_or_create(title='Кладовщик')
        pos_tech, _ = Position.objects.get_or_create(title='Технолог')
        pos_manager, _ = Position.objects.get_or_create(title='Менеджер')
        pos_seamstress, _ = Position.objects.get_or_create(title='Швея')

        # Employees
        emp1, _ = Employee.objects.get_or_create(full_name='Иванов И.И.', position=pos_store, salary=50000, address='ул. Ленина 1', phone='123456')
        emp2, _ = Employee.objects.get_or_create(full_name='Петрова А.А.', position=pos_manager, salary=70000, address='ул. Мира 5', phone='654321')
        emp3, _ = Employee.objects.get_or_create(full_name='Сидорова Е.Е.', position=pos_tech, salary=80000, address='ул. Гагарина 10', phone='987654')

        # Budget
        if not Budget.objects.exists():
            Budget.objects.create(amount=100000)

        # Raw Material
        raw_fabric, _ = RawMaterial.objects.get_or_create(name='Ткань Хлопок', unit=u_m, defaults={'quantity': 0, 'amount': 0})
        raw_thread, _ = RawMaterial.objects.get_or_create(name='Нитки Белые', unit=u_roll, defaults={'quantity': 0, 'amount': 0})
        raw_zipper, _ = RawMaterial.objects.get_or_create(name='Молния 50см', unit=u_pcs, defaults={'quantity': 0, 'amount': 0})
        raw_buttons, _ = RawMaterial.objects.get_or_create(name='Пуговицы', unit=u_pcs, defaults={'quantity': 0, 'amount': 0})

        # Finished Product
        prod_tshirt, _ = FinishedProduct.objects.get_or_create(name='Футболка Белая', unit=u_pcs, defaults={'quantity': 0, 'amount': 0})
        prod_hoodie, _ = FinishedProduct.objects.get_or_create(name='Худи Черное', unit=u_pcs, defaults={'quantity': 0, 'amount': 0})

        # Ingredients (Composition)
        # T-Shirt needs 1.5m fabric, 0.1 thread
        Ingredient.objects.get_or_create(product=prod_tshirt, raw_material=raw_fabric, defaults={'quantity': 1.5})
        Ingredient.objects.get_or_create(product=prod_tshirt, raw_material=raw_thread, defaults={'quantity': 0.1})
        
        # Hoodie needs 2.5m fabric, 0.2 thread, 1 zipper
        Ingredient.objects.get_or_create(product=prod_hoodie, raw_material=raw_fabric, defaults={'quantity': 2.5})
        Ingredient.objects.get_or_create(product=prod_hoodie, raw_material=raw_thread, defaults={'quantity': 0.2})
        Ingredient.objects.get_or_create(product=prod_hoodie, raw_material=raw_zipper, defaults={'quantity': 1.0})

        self.stdout.write(self.style.SUCCESS('Successfully populated database!'))
