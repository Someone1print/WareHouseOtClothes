from django.conf import settings
from django.db import migrations, models


def assign_director_role(apps, schema_editor):
    """Try to auto-mark a 'Директор' / 'Руководитель' position as director role
    so that the first user bootstrap is easier."""
    Position = apps.get_model('warehouse', 'Position')
    director_titles = ['Директор', 'Руководитель', 'Генеральный директор', 'CEO']
    for title in director_titles:
        for pos in Position.objects.filter(title__iexact=title):
            pos.role = 'director'
            pos.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0006_add_min_price_to_rawmaterial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='position',
            name='role',
            field=models.CharField(
                choices=[
                    ('director', 'Директор / Руководитель (полный доступ)'),
                    ('warehouse', 'Кладовщик (закупки, сырьё)'),
                    ('production', 'Производственник (производство, заявки)'),
                    ('sales', 'Продавец (продажи)'),
                    ('accountant', 'Бухгалтер (бюджет, зарплаты, кредиты)'),
                    ('none', 'Без особых прав'),
                ],
                default='none',
                max_length=20,
                verbose_name='Роль доступа',
            ),
        ),
        migrations.RunPython(assign_director_role, noop),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee', models.OneToOneField(
                    on_delete=models.deletion.PROTECT,
                    related_name='account',
                    to='warehouse.employee',
                    verbose_name='Сотрудник',
                )),
                ('user', models.OneToOneField(
                    on_delete=models.deletion.CASCADE,
                    related_name='profile',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Пользователь',
                )),
            ],
            options={
                'verbose_name': 'Аккаунт сотрудника',
                'verbose_name_plural': 'Аккаунты сотрудников',
            },
        ),
    ]
