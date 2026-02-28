from django.db import models
from django.core.exceptions import ValidationError

class Unit(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Наименование")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Единица измерения"
        verbose_name_plural = "Единицы измерения"


class Position(models.Model):
    title = models.CharField(max_length=100, unique=True, verbose_name="Название должности")

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

    def __str__(self):
        return self.name

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
