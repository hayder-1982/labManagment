from django.contrib import admin
from .models import Patient, IndividualTest, TestGroup, TestRequest, IndividualTestResult, TestGroupResult

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'gender', 'age', 'phone_number', 'created_at']
    list_filter = ['gender', 'created_at']
    search_fields = ['full_name', 'phone_number']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('المعلومات الأساسية', {
            'fields': ('full_name', 'date_of_birth', 'gender')
        }),
        ('معلومات الاتصال', {
            'fields': ('phone_number', 'address')
        }),
        ('معلومات النظام', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(IndividualTest)
class IndividualTestAdmin(admin.ModelAdmin):
    list_display = ['name', 'app_name','subclass','unit','display_order', 'normal_value_min_m', 'normal_value_max_m', 'normal_value_min_f', 'normal_value_max_f', 'normal_value_m', 'normal_value_f', 'price', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'app_name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    list_editable = ("display_order",'subclass')
    ordering = ("display_order",)
    fieldsets = (
        ('معلومات التحليل', {
            'fields': ('name','app_name', 'display_order', 'description','subclass', 'unit')
        }),
        ('القيم الطبيعية', {
            'fields': ( 'normal_value_min_m', 'normal_value_max_m', 'normal_value_min_f', 'normal_value_max_f', 'normal_value_m', 'normal_value_f',)
        }),
        ('التسعير والحالة', {
            'fields': ('price', 'is_active')
        }),
        ('معلومات النظام', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(TestGroup)
class TestGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'app_name', 'total_price', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['tests']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('معلومات المجموعة', {
            'fields': ('name','app_name', 'description')
        }),
        ('التحاليل المتضمنة', {
            'fields': ('tests',)
        }),
        ('التسعير والحالة', {
            'fields': ('total_price', 'is_active')
        }),
        ('معلومات النظام', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

class IndividualTestResultInline(admin.TabularInline):
    model = IndividualTestResult
    extra = 0
    readonly_fields = ['status', 'result_date']

class TestGroupResultInline(admin.TabularInline):
    model = TestGroupResult
    extra = 0
    readonly_fields = ['result_date']

@admin.register(TestRequest)
class TestRequestAdmin(admin.ModelAdmin):
    list_display = ['patient', 'status', 'request_date', 'get_total_price']
    list_filter = ['status', 'request_date']
    search_fields = ['patient__full_name']
    filter_horizontal = ['individual_tests', 'test_groups']
    readonly_fields = ['id', 'request_date', 'get_total_price']
    inlines = [IndividualTestResultInline, TestGroupResultInline]
    
    fieldsets = (
        ('معلومات الطلب', {
            'fields': ('patient', 'status', 'notes')
        }),
        ('التحاليل المطلوبة', {
            'fields': ('individual_tests', 'test_groups')
        }),
        ('معلومات النظام', {
            'fields': ('id', 'request_date', 'get_total_price', 'created_by'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # إذا كان طلب جديد
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(IndividualTestResult)
class IndividualTestResultAdmin(admin.ModelAdmin):
    list_display = ['test_request', 'individual_test', 'value', 'status', 'result_date']
    list_filter = ['status', 'result_date', 'individual_test']
    search_fields = ['test_request__patient__full_name', 'individual_test__name']
    readonly_fields = ['id', 'result_date', 'status']
    
    fieldsets = (
        ('معلومات النتيجة', {
            'fields': ('test_request', 'individual_test', 'value', 'status')
        }),
        ('ملاحظات إضافية', {
            'fields': ('notes',)
        }),
        ('معلومات النظام', {
            'fields': ('id', 'result_date', 'entered_by'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # إذا كانت نتيجة جديدة
            obj.entered_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(TestGroupResult)
class TestGroupResultAdmin(admin.ModelAdmin):
    list_display = ['test_request', 'test_group', 'status', 'result_date']
    list_filter = ['status', 'result_date', 'test_group']
    search_fields = ['test_request__patient__full_name', 'test_group__name']
    readonly_fields = ['id', 'result_date']
    
    fieldsets = (
        ('معلومات النتيجة', {
            'fields': ('test_request', 'test_group', 'status')
        }),
        ('ملاحظات إضافية', {
            'fields': ('notes',)
        }),
        ('معلومات النظام', {
            'fields': ('id', 'result_date'),
            'classes': ('collapse',)
        })
    )

# تخصيص عنوان لوحة الإدارة
admin.site.site_header = 'نظام إدارة المختبرات الطبية'
admin.site.site_title = 'إدارة المختبر'
admin.site.index_title = 'لوحة التحكم'

