from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import connection
from .models import Unit, Position, Employee, RawMaterial, FinishedProduct, Ingredient, Budget, ProductSale, Production, RawPurchase
from .forms import (UnitForm, PositionForm, EmployeeForm, RawMaterialForm, FinishedProductForm, IngredientForm, 
                    BudgetForm, ProductSaleForm, ProductionForm, RawPurchaseForm)

def index(request):
    return render(request, 'warehouse/index.html')

# --- Helper for generic CRUD ---
def generic_list(request, model, template_name, extra_context=None):
    items = model.objects.all()
    context = {'items': items}
    if extra_context:
        context.update(extra_context)
    return render(request, template_name, context)

def generic_form(request, form_class, template_name, instance=None, redirect_url='index'):
    if request.method == 'POST':
        form = form_class(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect(redirect_url)
    else:
        form = form_class(instance=instance)
    return render(request, template_name, {'form': form})

def generic_delete(request, model, pk, redirect_url):
    item = get_object_or_404(model, pk=pk)
    if request.method == 'POST':
        item.delete()
        return redirect(redirect_url)
    return render(request, 'warehouse/confirm_delete.html', {'item': item})

# --- Specific Views ---
# ... (I will implement specific views using the helpers or directly if needed)

# Budget
def budget_list(request):
    budget = Budget.objects.first()
    if not budget:
        # Create default if missing
        budget = Budget.objects.create(amount=100000)
    
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, 'Бюджет обновлен!')
            return redirect('budget_list')
    else:
        form = BudgetForm(instance=budget)
    
    return render(request, 'warehouse/budget.html', {'form': form, 'budget': budget})


# Purchase (Special Logic with Stored Procedure)
def purchase_create(request):
    if request.method == 'POST':
        form = RawPurchaseForm(request.POST)
        if form.is_valid():
            raw_id = form.cleaned_data['raw_material'].id
            quantity = form.cleaned_data['quantity']
            amount = form.cleaned_data['amount']
            employee_id = form.cleaned_data['employee'].id
            
            # Call Stored Procedure
            try:
                with connection.cursor() as cursor:
                    cursor.callproc('sp_create_purchase', [raw_id, quantity, amount, 'now()', employee_id])
                    result = cursor.fetchone()[0]
                
                if result == 0:
                    messages.success(request, "Сырьё успешно закуплено, бюджет обновлён")
                    return redirect('index')
                else:
                    messages.error(request, "Недостаточно средств в бюджете")
            except Exception as e:
                messages.error(request, f"Ошибка базы данных: {e}")
                
    else:
        form = RawPurchaseForm()
    
    # List of recent purchases for context
    purchases = RawPurchase.objects.all().order_by('-date')
    return render(request, 'warehouse/purchase_form.html', {'form': form, 'purchases': purchases})


# --- SQL View Reports ---

def view_raw_stock(request):
    query = "SELECT * FROM v_raw_material_stock"
    search = request.GET.get('search')
    params = []
    if search:
        query += " WHERE raw_name ILIKE %s"
        params.append(f"%{search}%")
    
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render(request, 'warehouse/view_raw_stock.html', {'results': results, 'search': search})

def view_product_stock(request):
    query = "SELECT * FROM v_finished_product_stock"
    search = request.GET.get('search')
    params = []
    if search:
        query += " WHERE product_name ILIKE %s"
        params.append(f"%{search}%")
    
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render(request, 'warehouse/view_product_stock.html', {'results': results, 'search': search})

def view_materials_needed(request):
    products = FinishedProduct.objects.all()
    selected_product_id = request.GET.get('product_id')
    n_units = request.GET.get('n_units', 1)
    
    results = []
    if selected_product_id:
        query = "SELECT * FROM v_materials_needed_for_production WHERE product_id = %s"
        with connection.cursor() as cursor:
            cursor.execute(query, [selected_product_id])
            columns = [col[0] for col in cursor.description]
            # Calculate for N units
            for row in cursor.fetchall():
                 item = dict(zip(columns, row))
                 item['needed_qty'] = item['ingredient_qty'] * float(n_units)
                 results.append(item)

    return render(request, 'warehouse/view_materials_needed.html', {
        'products': products, 
        'results': results, 
        'selected_product_id': int(selected_product_id) if selected_product_id else None,
        'n_units': n_units
    })


# --- Standard Views (Boilerplate) ---

# Units
def unit_list(request):
    return generic_list(request, Unit, 'warehouse/unit_list.html')
def unit_create(request):
    return generic_form(request, UnitForm, 'warehouse/form.html', redirect_url='unit_list')
def unit_update(request, pk):
    return generic_form(request, UnitForm, 'warehouse/form.html', instance=get_object_or_404(Unit, pk=pk), redirect_url='unit_list')
def unit_delete(request, pk):
    return generic_delete(request, Unit, pk, 'unit_list')

# Positions
def position_list(request):
    return generic_list(request, Position, 'warehouse/position_list.html')
def position_create(request):
    return generic_form(request, PositionForm, 'warehouse/form.html', redirect_url='position_list')
def position_update(request, pk):
    return generic_form(request, PositionForm, 'warehouse/form.html', instance=get_object_or_404(Position, pk=pk), redirect_url='position_list')
def position_delete(request, pk):
    return generic_delete(request, Position, pk, 'position_list')

# Employees
def employee_list(request):
    return generic_list(request, Employee, 'warehouse/employee_list.html')
def employee_create(request):
    return generic_form(request, EmployeeForm, 'warehouse/form.html', redirect_url='employee_list')
def employee_update(request, pk):
    return generic_form(request, EmployeeForm, 'warehouse/form.html', instance=get_object_or_404(Employee, pk=pk), redirect_url='employee_list')
def employee_delete(request, pk):
    return generic_delete(request, Employee, pk, 'employee_list')

# Raw Materials
def raw_material_list(request):
    return generic_list(request, RawMaterial, 'warehouse/raw_material_list.html')
def raw_material_create(request):
    return generic_form(request, RawMaterialForm, 'warehouse/form.html', redirect_url='raw_material_list')
def raw_material_update(request, pk):
    return generic_form(request, RawMaterialForm, 'warehouse/form.html', instance=get_object_or_404(RawMaterial, pk=pk), redirect_url='raw_material_list')
def raw_material_delete(request, pk):
    return generic_delete(request, RawMaterial, pk, 'raw_material_list')

# Finished Products
def finished_product_list(request):
    return generic_list(request, FinishedProduct, 'warehouse/finished_product_list.html')
def finished_product_create(request):
    return generic_form(request, FinishedProductForm, 'warehouse/form.html', redirect_url='finished_product_list')
def finished_product_update(request, pk):
    return generic_form(request, FinishedProductForm, 'warehouse/form.html', instance=get_object_or_404(FinishedProduct, pk=pk), redirect_url='finished_product_list')
def finished_product_delete(request, pk):
    return generic_delete(request, FinishedProduct, pk, 'finished_product_list')

# Ingredients
def ingredient_list(request):
    return generic_list(request, Ingredient, 'warehouse/ingredient_list.html')
def ingredient_create(request):
    return generic_form(request, IngredientForm, 'warehouse/form.html', redirect_url='ingredient_list')
def ingredient_update(request, pk):
    return generic_form(request, IngredientForm, 'warehouse/form.html', instance=get_object_or_404(Ingredient, pk=pk), redirect_url='ingredient_list')
def ingredient_delete(request, pk):
    return generic_delete(request, Ingredient, pk, 'ingredient_list')

# Production
def production_list(request):
    return generic_list(request, Production, 'warehouse/production_list.html')
def production_create(request):
    return generic_form(request, ProductionForm, 'warehouse/form.html', redirect_url='production_list')
# Production usually just created, but editing possible
def production_update(request, pk):
    return generic_form(request, ProductionForm, 'warehouse/form.html', instance=get_object_or_404(Production, pk=pk), redirect_url='production_list')
def production_delete(request, pk):
    return generic_delete(request, Production, pk, 'production_list')

# Sales
def sale_create(request):
    if request.method == 'POST':
        form = ProductSaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            # Logic to decrease product stock could be added here or via trigger
            # For this lab, prompt didn't strictly require trigger for sale, but let's just save.
            # However, prompt says "For each table do full CRUD".
            # Logic says: "FinishedProduct 1—M ProductSale"
            # If we want to be fancy we could decrease stock, but let's stick to basic CRUD + the REQUIRED purchase logic.
            sale.save()
            messages.success(request, "Продажа оформлена!")
            return redirect('sale_create')
    else:
        form = ProductSaleForm()
    
    sales = ProductSale.objects.all().order_by('-date')
    return render(request, 'warehouse/sale_form.html', {'form': form, 'sales': sales})
