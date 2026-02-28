from django import forms
from .models import Unit, Position, Employee, RawMaterial, FinishedProduct, Ingredient, Budget, ProductSale, Production

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = '__all__'

class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = '__all__'

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'

class RawMaterialForm(forms.ModelForm):
    class Meta:
        model = RawMaterial
        fields = '__all__'

class FinishedProductForm(forms.ModelForm):
    class Meta:
        model = FinishedProduct
        fields = '__all__'

class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredient
        fields = '__all__'

class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['amount']

class ProductSaleForm(forms.ModelForm):
    class Meta:
        model = ProductSale
        exclude = ['date']

class ProductionForm(forms.ModelForm):
    class Meta:
        model = Production
        exclude = ['date']

# Form for the stored procedure call (not a ModelForm)
class RawPurchaseForm(forms.Form):
    raw_material = forms.ModelChoiceField(queryset=RawMaterial.objects.all(), label="Сырьё")
    quantity = forms.FloatField(label="Количество")
    amount = forms.FloatField(label="Сумма закупки")
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), label="Сотрудник")
