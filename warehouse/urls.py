from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    
    # Generic CRUDs
    path('units/', views.unit_list, name='unit_list'),
    path('units/add/', views.unit_create, name='unit_create'),
    path('units/<int:pk>/edit/', views.unit_update, name='unit_update'),
    path('units/<int:pk>/delete/', views.unit_delete, name='unit_delete'),
    
    path('positions/', views.position_list, name='position_list'),
    path('positions/add/', views.position_create, name='position_create'),
    path('positions/<int:pk>/edit/', views.position_update, name='position_update'),
    path('positions/<int:pk>/delete/', views.position_delete, name='position_delete'),
    
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/edit/', views.employee_update, name='employee_update'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    
    path('raw_materials/', views.raw_material_list, name='raw_material_list'),
    path('raw_materials/add/', views.raw_material_create, name='raw_material_create'),
    path('raw_materials/<int:pk>/edit/', views.raw_material_update, name='raw_material_update'),
    path('raw_materials/<int:pk>/delete/', views.raw_material_delete, name='raw_material_delete'),
    
    path('finished_products/', views.finished_product_list, name='finished_product_list'),
    path('finished_products/add/', views.finished_product_create, name='finished_product_create'),
    path('finished_products/<int:pk>/edit/', views.finished_product_update, name='finished_product_update'),
    path('finished_products/<int:pk>/delete/', views.finished_product_delete, name='finished_product_delete'),
    
    path('ingredients/', views.ingredient_list, name='ingredient_list'),
    path('ingredients/add/', views.ingredient_create, name='ingredient_create'),
    path('ingredients/<int:pk>/edit/', views.ingredient_update, name='ingredient_update'),
    path('ingredients/<int:pk>/delete/', views.ingredient_delete, name='ingredient_delete'),
    
    path('production/', views.production_list, name='production_list'),
    path('production/add/', views.production_create, name='production_create'),
    path('production/<int:pk>/edit/', views.production_update, name='production_update'),
    path('production/<int:pk>/delete/', views.production_delete, name='production_delete'),

    path('sale/add/', views.sale_create, name='sale_create'),
    
    # Specific Logic
    path('budget/', views.budget_list, name='budget_list'),
    path('purchase/add/', views.purchase_create, name='purchase_create'),
    
    # SQL Views
    path('view/raw_stock/', views.view_raw_stock, name='view_raw_stock'),
    path('view/product_stock/', views.view_product_stock, name='view_product_stock'),
    path('view/materials_needed/', views.view_materials_needed, name='view_materials_needed'),
]
