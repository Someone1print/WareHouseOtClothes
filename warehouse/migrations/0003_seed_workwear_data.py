from django.db import migrations

def seed_workwear_data(apps, schema_editor):
    # Get models from historical version
    Unit = apps.get_model('warehouse', 'Unit')
    Position = apps.get_model('warehouse', 'Position')
    Employee = apps.get_model('warehouse', 'Employee')
    RawMaterial = apps.get_model('warehouse', 'RawMaterial')
    FinishedProduct = apps.get_model('warehouse', 'FinishedProduct')
    Ingredient = apps.get_model('warehouse', 'Ingredient')
    Budget = apps.get_model('warehouse', 'Budget')

    # 1. Budget
    if not Budget.objects.exists():
        Budget.objects.create(amount=500000.00)
    
    # 2. Units
    u_m, _ = Unit.objects.get_or_create(name='м')
    u_kg, _ = Unit.objects.get_or_create(name='кг')
    u_pcs, _ = Unit.objects.get_or_create(name='шт')
    u_roll, _ = Unit.objects.get_or_create(name='рулон')

    # 3. Positions
    p_foreman, _ = Position.objects.get_or_create(title='Начальник цеха')
    p_cutter, _ = Position.objects.get_or_create(title='Закройщик')
    p_seamstress, _ = Position.objects.get_or_create(title='Швея-мотористка')
    p_tech, _ = Position.objects.get_or_create(title='Технолог')

    # 4. Employees
    Employee.objects.get_or_create(full_name='Смирнов Алексей Петрович', position=p_foreman, salary=85000, address='ул. Заводская 12', phone='89001112233')
    Employee.objects.get_or_create(full_name='Козлова Марина Ивановна', position=p_cutter, salary=55000, address='пр. Ленина 45', phone='89004445566')
    Employee.objects.get_or_create(full_name='Васильева Елена Сергеевна', position=p_seamstress, salary=45000, address='ул. Мира 8', phone='89007778899')

    # 5. Raw Materials (Specialized Workwear)
    rm_oxford, _ = RawMaterial.objects.get_or_create(name='Ткань Оксфорд 600D (синяя)', unit=u_m, defaults={'quantity': 0, 'amount': 0})
    rm_tarpaulin, _ = RawMaterial.objects.get_or_create(name='Брезент огнеупорный', unit=u_m, defaults={'quantity': 0, 'amount': 0})
    rm_reflective, _ = RawMaterial.objects.get_or_create(name='Лента светоотражающая 50мм', unit=u_m, defaults={'quantity': 0, 'amount': 0})
    rm_zipper, _ = RawMaterial.objects.get_or_create(name='Молния тракторная усиленная', unit=u_pcs, defaults={'quantity': 0, 'amount': 0})
    rm_thread, _ = RawMaterial.objects.get_or_create(name='Нитки армированные 45ЛЛ', unit=u_roll, defaults={'quantity': 0, 'amount': 0})
    rm_buttons, _ = RawMaterial.objects.get_or_create(name='Пуговицы форменные', unit=u_pcs, defaults={'quantity': 0, 'amount': 0})

    # 6. Finished Products (Workwear)
    fp_suit, _ = FinishedProduct.objects.get_or_create(name='Костюм рабочий "Мастер" (куртка+брюки)', unit=u_pcs, defaults={'quantity': 0, 'amount': 0})
    fp_vest, _ = FinishedProduct.objects.get_or_create(name='Жилет сигнальный (оранжевый)', unit=u_pcs, defaults={'quantity': 0, 'amount': 0})
    fp_coverall, _ = FinishedProduct.objects.get_or_create(name='Комбинезон защитный "Сварщик"', unit=u_pcs, defaults={'quantity': 0, 'amount': 0})

    # 7. Ingredients
    # Composition for "Master" Suit
    Ingredient.objects.get_or_create(product=fp_suit, raw_material=rm_oxford, defaults={'quantity': 3.5}) # 3.5m fabric
    Ingredient.objects.get_or_create(product=fp_suit, raw_material=rm_zipper, defaults={'quantity': 1})
    Ingredient.objects.get_or_create(product=fp_suit, raw_material=rm_thread, defaults={'quantity': 0.2}) # 0.2 roll
    Ingredient.objects.get_or_create(product=fp_suit, raw_material=rm_reflective, defaults={'quantity': 2.0})

    # Composition for Signal Vest
    Ingredient.objects.get_or_create(product=fp_vest, raw_material=rm_oxford, defaults={'quantity': 0.8})
    Ingredient.objects.get_or_create(product=fp_vest, raw_material=rm_reflective, defaults={'quantity': 3.0})
    Ingredient.objects.get_or_create(product=fp_vest, raw_material=rm_thread, defaults={'quantity': 0.05})

    # Composition for Welder Coverall
    Ingredient.objects.get_or_create(product=fp_coverall, raw_material=rm_tarpaulin, defaults={'quantity': 4.0})
    Ingredient.objects.get_or_create(product=fp_coverall, raw_material=rm_buttons, defaults={'quantity': 8})
    Ingredient.objects.get_or_create(product=fp_coverall, raw_material=rm_thread, defaults={'quantity': 0.3})


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0002_create_sql_logic'),
    ]

    operations = [
        migrations.RunPython(seed_workwear_data),
    ]
