from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Unit(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Наименование")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Единица измерения"
        verbose_name_plural = "Единицы измерения"


class Position(models.Model):
    ROLE_DIRECTOR = 'director'
    ROLE_WAREHOUSE = 'warehouse'
    ROLE_PRODUCTION = 'production'
    ROLE_SALES = 'sales'
    ROLE_ACCOUNTANT = 'accountant'
    ROLE_NONE = 'none'

    ROLE_CHOICES = [
        (ROLE_DIRECTOR, 'Директор / Руководитель (полный доступ)'),
        (ROLE_WAREHOUSE, 'Кладовщик (закупки, сырьё)'),
        (ROLE_PRODUCTION, 'Производственник (производство, заявки)'),
        (ROLE_SALES, 'Продавец (продажи)'),
        (ROLE_ACCOUNTANT, 'Бухгалтер (бюджет, зарплаты, кредиты)'),
        (ROLE_NONE, 'Без особых прав'),
    ]

    title = models.CharField(max_length=100, unique=True, verbose_name="Название должности")
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_NONE,
        verbose_name="Роль доступа",
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"


class Employee(models.Model):
    full_name = models.CharField(max_length=200, verbose_name="ФИО")
    position = models.ForeignKey(Position, on_delete=models.PROTECT, verbose_name="Должность")
    salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Оклад")
    address = models.CharField(max_length=255, verbose_name="Адрес", blank=True, null=True)
    phone = models.CharField(max_length=20, verbose_name="Телефон", blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} ({self.position})"

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"


class RawMaterial(models.Model):
    name = models.CharField(max_length=200, verbose_name="Наименование сырья")
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, verbose_name="Ед. изм.")
    quantity = models.FloatField(default=0.0, verbose_name="Остаток")
    amount = models.FloatField(default=0.0, verbose_name="Общая стоимость остатка")
    min_price = models.FloatField(default=0.0, verbose_name="Мин. цена за единицу", help_text="Минимальная / базовая цена закупки за 1 единицу")

    def __str__(self):
        return self.name

    @property
    def unit_cost(self):
        """Actual cost per unit. Falls back to min_price if stock is 0."""
        if self.quantity > 0:
            return self.amount / self.quantity
        return self.min_price

    class Meta:
        verbose_name = "Сырьё"
        verbose_name_plural = "Сырьё"


class FinishedProduct(models.Model):
    name = models.CharField(max_length=200, verbose_name="Наименование продукции")
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, verbose_name="Ед. изм.")
    quantity = models.FloatField(default=0.0, verbose_name="Остаток")
    amount = models.FloatField(default=0.0, verbose_name="Общая стоимость остатка")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Готовая продукция"
        verbose_name_plural = "Готовая продукция"


class Ingredient(models.Model):
    product = models.ForeignKey(FinishedProduct, on_delete=models.CASCADE, verbose_name="Продукция")
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT, verbose_name="Сырьё")
    quantity = models.FloatField(verbose_name="Количество на 1 ед. продукции")

    class Meta:
        unique_together = ('product', 'raw_material')
        verbose_name = "Ингредиент (Состав)"
        verbose_name_plural = "Ингредиенты (Состав)"

    def __str__(self):
        return f"{self.raw_material} для {self.product}"


class Budget(models.Model):
    amount = models.FloatField(verbose_name="Сумма бюджета (общая)")

    def save(self, *args, **kwargs):
        if not self.pk and Budget.objects.exists():
            raise ValidationError('There can be only one Budget instance')
        return super(Budget, self).save(*args, **kwargs)

    def __str__(self):
        return f"Бюджет: {self.amount}"

    class Meta:
        verbose_name = "Бюджет"
        verbose_name_plural = "Бюджет"


class RawPurchase(models.Model):
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT, verbose_name="Сырьё")
    quantity = models.FloatField(verbose_name="Количестсво")
    amount = models.FloatField(verbose_name="Сумма закупки")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, verbose_name="Сотрудник")

    class Meta:
        verbose_name = "Закупка сырья"
        verbose_name_plural = "Закупки сырья"


class ProductSale(models.Model):
    product = models.ForeignKey(FinishedProduct, on_delete=models.PROTECT, verbose_name="Продукция")
    quantity = models.FloatField(verbose_name="Количество")
    amount = models.FloatField(verbose_name="Сумма продажи")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, verbose_name="Сотрудник")

    class Meta:
        verbose_name = "Продажа продукции"
        verbose_name_plural = "Продажи продукции"


class Production(models.Model):
    product = models.ForeignKey(FinishedProduct, on_delete=models.PROTECT, verbose_name="Продукция")
    quantity = models.FloatField(verbose_name="Количество произведенного")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, verbose_name="Сотрудник")

    class Meta:
        verbose_name = "Производство"
        verbose_name_plural = "Производство"


class SalaryPayment(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, verbose_name="Сотрудник")
    amount = models.FloatField(verbose_name="Сумма выплаты")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата выплаты")

    class Meta:
        verbose_name = "Выплата зарплаты"
        verbose_name_plural = "Выплаты зарплаты"


class BusinessLoan(models.Model):
    amount = models.FloatField(verbose_name="Сумма кредита")
    date_taken = models.DateTimeField(auto_now_add=True, verbose_name="Дата получения")

    def clean(self):
        if not self.pk and BusinessLoan.objects.count() >= 3:
            raise ValidationError('Достигнут лимит кредитов (максимум 3).')

    def save(self, *args, **kwargs):
        self.clean()
        super(BusinessLoan, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Бизнес-кредит"
        verbose_name_plural = "Бизнес-кредиты"


class ProductionRequest(models.Model):
    STATUS_CREATED = 'Создана'
    STATUS_CHECKING_RAW = 'На проверке наличия сырья'
    STATUS_PURCHASING = 'На процессе закупки сырья'
    STATUS_PRODUCTION = 'На процессе производства'
    STATUS_SALE = 'На процессе продажи'
    STATUS_COMPLETED = 'Выполнена'
    STATUS_ERROR = 'Ошибка'

    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создана'),
        (STATUS_CHECKING_RAW, 'На проверке наличия сырья'),
        (STATUS_PURCHASING, 'На процессе закупки сырья'),
        (STATUS_PRODUCTION, 'На процессе производства'),
        (STATUS_SALE, 'На процессе продажи'),
        (STATUS_COMPLETED, 'Выполнена'),
        (STATUS_ERROR, 'Ошибка'),
    ]

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата последнего обновления")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_CREATED, verbose_name="Статус")
    applicant_name = models.CharField(max_length=200, verbose_name="ФИО заявителя")
    product = models.ForeignKey('FinishedProduct', on_delete=models.CASCADE, verbose_name="Готовая продукция")
    quantity = models.FloatField(verbose_name="Количество продукции")
    rejection_reason = models.TextField(blank=True, null=True, verbose_name="Причина отказа")

    def __str__(self):
        return f"Заявка №{self.id} от {self.applicant_name} ({self.status})"

    class Meta:
        verbose_name = "Заявка на производство"
        verbose_name_plural = "Заявки на производство"


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="Пользователь",
    )
    employee = models.OneToOneField(
        Employee,
        on_delete=models.PROTECT,
        related_name='account',
        verbose_name="Сотрудник",
    )

    def __str__(self):
        return f"{self.user.username} → {self.employee.full_name}"

    @property
    def role(self):
        return self.employee.position.role

    @property
    def is_director(self):
        return self.role == Position.ROLE_DIRECTOR

    class Meta:
        verbose_name = "Аккаунт сотрудника"
        verbose_name_plural = "Аккаунты сотрудников"

