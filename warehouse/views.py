from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import connection
from .models import Unit, Position, Employee, RawMaterial, FinishedProduct, Ingredient, Budget, ProductSale, Production, RawPurchase, SalaryPayment, BusinessLoan
from .forms import (UnitForm, PositionForm, EmployeeForm, RawMaterialForm, FinishedProductForm, IngredientForm,
                    BudgetForm, ProductSaleForm, ProductionForm, RawPurchaseForm, SalaryPaymentForm, BusinessLoanForm)
from .permissions import director_required, role_required, get_employee


def _resolve_employee(request):
    """Сотрудник, от лица которого выполняется операция.
    Для обычного пользователя — его привязанный Employee, для суперюзера —
    либо его профиль, либо первый сотрудник в системе (fallback для бутстрапа).
    """
    emp = get_employee(request.user)
    if emp:
        return emp
    if request.user.is_superuser:
        return Employee.objects.first()
    return None


@login_required
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
@role_required(Position.ROLE_ACCOUNTANT)
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
@role_required(Position.ROLE_WAREHOUSE)
def purchase_create(request):
    if request.method == 'POST':
        form = RawPurchaseForm(request.POST)
        if form.is_valid():
            emp = _resolve_employee(request)
            if not emp:
                messages.error(request, "Ваш аккаунт не привязан к сотруднику.")
                return redirect('index')
            raw_id = form.cleaned_data['raw_material'].id
            quantity = form.cleaned_data['quantity']
            amount = form.cleaned_data['amount']
            employee_id = emp.id
            
            # Call Stored Procedure
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SET NOCOUNT ON;
                        DECLARE @res INT;
                        EXEC sp_create_purchase %s, %s, %s, %s, %s, @res OUTPUT;
                        SELECT @res;
                    """, [raw_id, quantity, amount, timezone.now(), employee_id])
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
    
    # Prepare material price data for JS suggestions
    materials_data = {m.id: m.min_price for m in RawMaterial.objects.all()}
    
    # List of recent purchases for context
    purchases = RawPurchase.objects.all().order_by('-date')
    return render(request, 'warehouse/purchase_form.html', {
        'form': form, 
        'purchases': purchases,
        'materials_data': materials_data
    })


# --- SQL View Reports ---

@role_required(Position.ROLE_WAREHOUSE, Position.ROLE_PRODUCTION, Position.ROLE_ACCOUNTANT)
def view_raw_stock(request):
    query = "SELECT * FROM v_raw_material_stock"
    search = request.GET.get('search')
    params = []
    if search:
        query += " WHERE raw_name LIKE %s"
        params.append(f"%{search}%")
    
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render(request, 'warehouse/view_raw_stock.html', {'results': results, 'search': search})

@role_required(Position.ROLE_SALES, Position.ROLE_PRODUCTION, Position.ROLE_ACCOUNTANT)
def view_product_stock(request):
    query = "SELECT * FROM v_finished_product_stock"
    search = request.GET.get('search')
    params = []
    if search:
        query += " WHERE product_name LIKE %s"
        params.append(f"%{search}%")
    
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render(request, 'warehouse/view_product_stock.html', {'results': results, 'search': search})

@role_required(Position.ROLE_WAREHOUSE, Position.ROLE_PRODUCTION)
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
                 try:
                     raw = RawMaterial.objects.get(pk=item['raw_id'])
                     item['available_qty'] = raw.quantity
                 except RawMaterial.DoesNotExist:
                     item['available_qty'] = 0
                     
                 item['is_enough'] = item['available_qty'] >= item['needed_qty']
                 results.append(item)

    return render(request, 'warehouse/view_materials_needed.html', {
        'products': products, 
        'results': results, 
        'selected_product_id': int(selected_product_id) if selected_product_id else None,
        'n_units': n_units
    })

# --- Standard Views (Boilerplate) ---

# Units (только директор)
@director_required
def unit_list(request):
    return generic_list(request, Unit, 'warehouse/unit_list.html')
@director_required
def unit_create(request):
    return generic_form(request, UnitForm, 'warehouse/form.html', redirect_url='unit_list')
@director_required
def unit_update(request, pk):
    return generic_form(request, UnitForm, 'warehouse/form.html', instance=get_object_or_404(Unit, pk=pk), redirect_url='unit_list')
@director_required
def unit_delete(request, pk):
    return generic_delete(request, Unit, pk, 'unit_list')

# Positions (только директор)
@director_required
def position_list(request):
    return generic_list(request, Position, 'warehouse/position_list.html')
@director_required
def position_create(request):
    return generic_form(request, PositionForm, 'warehouse/form.html', redirect_url='position_list')
@director_required
def position_update(request, pk):
    return generic_form(request, PositionForm, 'warehouse/form.html', instance=get_object_or_404(Position, pk=pk), redirect_url='position_list')
@director_required
def position_delete(request, pk):
    return generic_delete(request, Position, pk, 'position_list')

# Employees (только директор)
@director_required
def employee_list(request):
    return generic_list(request, Employee, 'warehouse/employee_list.html')
@director_required
def employee_create(request):
    return generic_form(request, EmployeeForm, 'warehouse/form.html', redirect_url='employee_list')
@director_required
def employee_update(request, pk):
    return generic_form(request, EmployeeForm, 'warehouse/form.html', instance=get_object_or_404(Employee, pk=pk), redirect_url='employee_list')
@director_required
def employee_delete(request, pk):
    return generic_delete(request, Employee, pk, 'employee_list')

# Raw Materials (кладовщик + директор)
@role_required(Position.ROLE_WAREHOUSE)
def raw_material_list(request):
    return generic_list(request, RawMaterial, 'warehouse/raw_material_list.html')
@director_required
def raw_material_create(request):
    return generic_form(request, RawMaterialForm, 'warehouse/form.html', redirect_url='raw_material_list')
@director_required
def raw_material_update(request, pk):
    return generic_form(request, RawMaterialForm, 'warehouse/form.html', instance=get_object_or_404(RawMaterial, pk=pk), redirect_url='raw_material_list')
@director_required
def raw_material_delete(request, pk):
    return generic_delete(request, RawMaterial, pk, 'raw_material_list')

# Finished Products (продавец, производство — просмотр; директор — управление)
@role_required(Position.ROLE_SALES, Position.ROLE_PRODUCTION)
def finished_product_list(request):
    return generic_list(request, FinishedProduct, 'warehouse/finished_product_list.html')
@director_required
def finished_product_create(request):
    return generic_form(request, FinishedProductForm, 'warehouse/form.html', redirect_url='finished_product_list')
@director_required
def finished_product_update(request, pk):
    return generic_form(request, FinishedProductForm, 'warehouse/form.html', instance=get_object_or_404(FinishedProduct, pk=pk), redirect_url='finished_product_list')
@director_required
def finished_product_delete(request, pk):
    return generic_delete(request, FinishedProduct, pk, 'finished_product_list')

# Ingredients / составы (производство — просмотр; директор — управление)
@role_required(Position.ROLE_PRODUCTION)
def ingredient_list(request):
    return generic_list(request, Ingredient, 'warehouse/ingredient_list.html')
@director_required
def ingredient_create(request):
    return generic_form(request, IngredientForm, 'warehouse/form.html', redirect_url='ingredient_list')
@director_required
def ingredient_update(request, pk):
    return generic_form(request, IngredientForm, 'warehouse/form.html', instance=get_object_or_404(Ingredient, pk=pk), redirect_url='ingredient_list')
@director_required
def ingredient_delete(request, pk):
    return generic_delete(request, Ingredient, pk, 'ingredient_list')

# Production
from django.utils.safestring import mark_safe

@role_required(Position.ROLE_PRODUCTION)
def production_list(request):
    return generic_list(request, Production, 'warehouse/production_list.html')

@role_required(Position.ROLE_PRODUCTION)
def production_create(request):
    if request.method == 'POST':
        form = ProductionForm(request.POST)
        if form.is_valid():
            emp = _resolve_employee(request)
            if not emp:
                messages.error(request, "Ваш аккаунт не привязан к сотруднику.")
                return redirect('index')
            production = form.save(commit=False)
            production.employee = emp
            product = production.product
            qty = production.quantity
            
            ingredients = product.ingredient_set.all()
            missing = []
            
            for ing in ingredients:
                needed = ing.quantity * qty
                if ing.raw_material.quantity < needed:
                    missing_str = f"<b>{ing.raw_material.name}</b> &mdash; Нужно: {needed:,.2f}, Доступно: {ing.raw_material.quantity:,.2f}".replace(',', ' ')
                    missing.append(missing_str)
            
            if missing:
                error_msg = "Недостаточно сырья для производства:<ul class='mt-2 mb-0'><li>" + "</li><li>".join(missing) + "</li></ul>"
                messages.error(request, mark_safe(error_msg))
            else:
                for ing in ingredients:
                    needed = ing.quantity * qty
                    raw = ing.raw_material
                    if raw.quantity > 0:
                        unit_cost = raw.amount / raw.quantity
                        raw.quantity -= needed
                        raw.amount -= needed * unit_cost
                        raw.save()
                    elif raw.quantity >= needed:
                        raw.quantity -= needed
                        raw.save()
                
                product.quantity += qty
                product.save()
                production.save()
                messages.success(request, f"Успешно произведено {qty} ед. {product.name}.")
                return redirect('production_list')
    else:
        form = ProductionForm()
    return render(request, 'warehouse/form.html', {'form': form, 'title': 'Новое производство'})
# Production usually just created, but editing possible
@director_required
def production_update(request, pk):
    return generic_form(request, ProductionForm, 'warehouse/form.html', instance=get_object_or_404(Production, pk=pk), redirect_url='production_list')
@director_required
def production_delete(request, pk):
    return generic_delete(request, Production, pk, 'production_list')

# Sales
@role_required(Position.ROLE_SALES)
def sale_create(request):
    if request.method == 'POST':
        form = ProductSaleForm(request.POST)
        if form.is_valid():
            emp = _resolve_employee(request)
            if not emp:
                messages.error(request, "Ваш аккаунт не привязан к сотруднику.")
                return redirect('index')
            sale = form.save(commit=False)
            sale.employee = emp
            product = sale.product
            qty = sale.quantity

            if product.quantity < qty:
                messages.error(request, "Недостаточно готовой продукции на складе!")
                return redirect('sale_create')

            # Calculate sale price automatically: unit_cost * 1.30 * qty
            unit_cost = product.amount / product.quantity if product.quantity > 0 else 0
            sale_amount = unit_cost * qty * 1.30
            sale.amount = sale_amount

            product.quantity -= qty
            product.amount -= unit_cost * qty  # deduct cost in proportion
            product.save()

            budget = Budget.objects.first()
            if budget:
                budget.amount += sale_amount
                budget.save()

            sale.save()
            messages.success(request, f"Продажа оформлена. Бюджет пополнен на {sale_amount:,.2f} KGS (себестоимость + 30%).".replace(',', ' '))
            return redirect('sale_create')
    else:
        form = ProductSaleForm()
    
    sales = ProductSale.objects.all().order_by('-date')
    return render(request, 'warehouse/sale_form.html', {'form': form, 'sales': sales})

# Salaries (бухгалтер)
@role_required(Position.ROLE_ACCOUNTANT)
def salary_list(request):
    return generic_list(request, SalaryPayment, 'warehouse/salary_list.html')

@role_required(Position.ROLE_ACCOUNTANT)
def salary_create(request):
    if request.method == 'POST':
        form = SalaryPaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            budget = Budget.objects.first()
            if budget and budget.amount >= payment.amount:
                budget.amount -= payment.amount
                budget.save()
                payment.save()
                messages.success(request, "Зарплата выплачена. Бюджет уменьшен.")
            else:
                messages.error(request, "Недостаточно средств в бюджете для выплаты зарплаты.")
            return redirect('salary_list')
    else:
        form = SalaryPaymentForm()
    return render(request, 'warehouse/form.html', {'form': form, 'title': 'Выплата зарплаты'})

@role_required(Position.ROLE_ACCOUNTANT)
def salary_update(request, pk):
    return generic_form(request, SalaryPaymentForm, 'warehouse/form.html', instance=get_object_or_404(SalaryPayment, pk=pk), redirect_url='salary_list')

@director_required
def salary_delete(request, pk):
    return generic_delete(request, SalaryPayment, pk, 'salary_list')


# Loans (бухгалтер)
@role_required(Position.ROLE_ACCOUNTANT)
def loan_list(request):
    return generic_list(request, BusinessLoan, 'warehouse/loan_list.html')

@role_required(Position.ROLE_ACCOUNTANT)
def loan_create(request):
    if BusinessLoan.objects.count() >= 3:
        messages.error(request, "Достигнут лимит кредитов (максимум 3).")
        return redirect('loan_list')
        
    if request.method == 'POST':
        form = BusinessLoanForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            budget = Budget.objects.first()
            if budget:
                budget.amount += loan.amount
                budget.save()
            loan.save()
            messages.success(request, "Кредит получен. Бюджет пополнен.")
            return redirect('loan_list')
    else:
        form = BusinessLoanForm()
    return render(request, 'warehouse/form.html', {'form': form, 'title': 'Новый кредит'})

@role_required(Position.ROLE_ACCOUNTANT)
def loan_update(request, pk):
    return generic_form(request, BusinessLoanForm, 'warehouse/form.html', instance=get_object_or_404(BusinessLoan, pk=pk), redirect_url='loan_list')

@director_required
def loan_delete(request, pk):
    return generic_delete(request, BusinessLoan, pk, 'loan_list')

@role_required(Position.ROLE_ACCOUNTANT)
def loan_payoff(request, pk):
    loan = get_object_or_404(BusinessLoan, pk=pk)
    if request.method == 'POST':
        budget = Budget.objects.first()
        if budget and budget.amount >= loan.amount:
            budget.amount -= loan.amount
            budget.save()
            loan.delete()
            messages.success(request, "Кредит успешно погашен. Бюджет уменьшен.")
        else:
            messages.error(request, f"Недостаточно средств в бюджете для погашения кредита (нужно: {loan.amount:,.2f} KGS).".replace(',', ' '))
        return redirect('loan_list')
    # If GET, you could render a confirmation page, but we'll submit POST via form directly.
    return redirect('loan_list')

from django.db.models import Sum, Count
import json
from django.core.serializers.json import DjangoJSONEncoder

# Analytics Dashboard
@role_required(Position.ROLE_ACCOUNTANT)
def analytics_dashboard(request):
    sales = ProductSale.objects.select_related('product', 'employee').order_by('-date')
    purchases = RawPurchase.objects.select_related('raw_material', 'employee').order_by('-date')
    salaries = SalaryPayment.objects.select_related('employee').order_by('-date')
    
    # Aggregations for Charts
    # 1. Top Sold Products
    top_products_qs = sales.values('product__name').annotate(total_qty=Sum('quantity'), total_revenue=Sum('amount')).order_by('-total_revenue')[:5]
    top_products_labels = [item['product__name'] for item in top_products_qs]
    top_products_data = [float(item['total_revenue']) for item in top_products_qs]
    
    # 2. Revenue vs Expenses overall
    total_sales = sales.aggregate(Sum('amount'))['amount__sum'] or 0
    total_purchases = purchases.aggregate(Sum('amount'))['amount__sum'] or 0
    total_salaries = salaries.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expenses = total_purchases + total_salaries

    context = {
        'sales': sales,
        'purchases': purchases,
        'salaries': salaries,
        'chart_top_products_labels': json.dumps(top_products_labels, cls=DjangoJSONEncoder),
        'chart_top_products_data': json.dumps(top_products_data, cls=DjangoJSONEncoder),
        'total_sales': float(total_sales),
        'total_expenses': float(total_expenses),
        'total_purchases': float(total_purchases),
        'total_salaries': float(total_salaries),
    }
    return render(request, 'warehouse/analytics_dashboard.html', context)


# --- Production Requests ---
from .models import ProductionRequest
from .forms import ProductionRequestForm

def process_production_request(req, acting_employee=None):
    try:
        req.status = ProductionRequest.STATUS_CHECKING_RAW
        req.save()

        product = req.product
        qty = req.quantity
        ingredients = product.ingredient_set.select_related('raw_material').all()
        
        # 1. На проверке наличия сырья
        missing_materials = []
        total_cost_of_production = 0
        
        for ing in ingredients:
            needed = ing.quantity * qty
            available = ing.raw_material.quantity
            
            # Use the model property which handles fallback to min_price
            unit_cost = ing.raw_material.unit_cost
            total_cost_of_production += needed * unit_cost

            if needed > available:
                missing_qty = needed - available
                missing_materials.append({
                    'raw_material': ing.raw_material,
                    'qty': missing_qty,
                    'cost': missing_qty * unit_cost
                })

        # 2. На процессе закупки сырья
        if missing_materials:
            req.status = ProductionRequest.STATUS_PURCHASING
            req.save()
            
            total_purchase_cost = sum(m['cost'] for m in missing_materials)
            budget = Budget.objects.first()
            
            if not budget or budget.amount < total_purchase_cost:
                # Оставляем статус на текущем этапе закупки
                def fmt(v):
                    return f"{float(v):,.2f}".replace(',', ' ')
                
                missing_details = ", ".join([f"{m['raw_material'].name} ({fmt(m['qty'])} ед.)" for m in missing_materials])
                req.rejection_reason = f"Не хватило бюджета на закупку сырья. Требуется: {fmt(total_purchase_cost)}. Недостающие товары: {missing_details}"
                req.save()
                return
            
            employee = acting_employee or Employee.objects.first()
            if not employee:
                req.rejection_reason = "Отсутствуют сотрудники для проведения закупки."
                req.save()
                return

            budget.amount -= total_purchase_cost
            budget.save()
            
            for m in missing_materials:
                raw = m['raw_material']
                RawPurchase.objects.create(
                    raw_material=raw,
                    quantity=m['qty'],
                    amount=m['cost'],
                    employee=employee
                )
                raw.quantity += m['qty']
                raw.amount += m['cost']
                raw.save()

        # 3. На процессе производства
        req.status = ProductionRequest.STATUS_PRODUCTION
        req.save()
        
        # Deduct raw materials exactly
        for ing in ingredients:
            needed = ing.quantity * qty
            raw = ing.raw_material
            unit_cost = raw.unit_cost
            raw.quantity -= needed
            raw.amount -= needed * unit_cost
            raw.save()

        employee = Employee.objects.first()
        if not employee:
            req.rejection_reason = "Отсутствуют сотрудники для проведения производства."
            req.save()
            return

        Production.objects.create(
            product=product,
            quantity=qty,
            employee=employee
        )
        product.quantity += qty
        product.amount += total_cost_of_production
        product.save()

        # 4. На процессе продажи
        req.status = ProductionRequest.STATUS_SALE
        req.save()

        sale_price = total_cost_of_production * 1.30
        budget = Budget.objects.first()
        if budget:
            budget.amount += sale_price
            budget.save()
        else:
            req.rejection_reason = "Отсутствует системный счет (бюджет) для пополнения."
            req.save()
            return

        ProductSale.objects.create(
            product=product,
            quantity=qty,
            amount=sale_price,
            employee=employee
        )
        product.quantity -= qty
        product.amount -= total_cost_of_production
        product.save()

        # 5. Выполнена
        req.status = ProductionRequest.STATUS_COMPLETED
        req.save()

    except Exception as e:
        req.status = ProductionRequest.STATUS_ERROR
        req.rejection_reason = f"Системный сбой: {str(e)}"
        req.save()


@role_required(Position.ROLE_PRODUCTION)
def production_request_list(request):
    requests = ProductionRequest.objects.all().order_by('-created_at')
    return render(request, 'warehouse/production_request_list.html', {'requests': requests})

@role_required(Position.ROLE_PRODUCTION)
def production_request_create(request):
    if request.method == 'POST':
        form = ProductionRequestForm(request.POST)
        if form.is_valid():
            req_obj = form.save()
            process_production_request(req_obj, acting_employee=_resolve_employee(request))
            return redirect('production_request_list')
    else:
        form = ProductionRequestForm()
    return render(request, 'warehouse/production_request_form.html', {'form': form, 'title': 'Новая заявка на производство'})

