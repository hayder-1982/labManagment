from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import random
from datetime import datetime
from datetime import date
from django.utils import timezone
from django.core.exceptions import ValidationError

class Patient(models.Model):
    GENDER_CHOICES = [('M', 'ذكر'), ('F', 'أنثى')]
    
    id = models.AutoField(primary_key=True)
    barcode = models.CharField(max_length=100, null=True, blank=True, unique=True)
    full_name = models.CharField(max_length=200, verbose_name='الاسم الكامل')
    date_of_birth = models.DateField(verbose_name='تاريخ الميلاد', null=True, blank=True)
    age = models.PositiveIntegerField(verbose_name='العمر', null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='الجنس')
    phone_number = models.CharField(max_length=15, verbose_name='رقم الهاتف', null=True, blank=True)
    address = models.TextField(verbose_name='العنوان', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ التسجيل')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')

    class Meta:
        verbose_name = 'مريض'
        verbose_name_plural = 'المرضى'
        ordering = ['-created_at']

    def __str__(self):
        return self.full_name

    def calculate_age(self):
        """حساب العمر من تاريخ الميلاد"""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    def estimate_birthdate_from_age(self):
        """إيجاد تاريخ الميلاد التقريبي من العمر"""
        if self.age:
            today = date.today()
            approx_year = today.year - self.age
            return date(approx_year, 7, 1)  # يوم/شهر افتراضي
        return None
     
    def clean(self):
        super().clean()
        if not self.date_of_birth and not self.age:
            raise ValidationError("يجب إدخال العمر أو تاريخ الميلاد على الأقل.")

    def save(self, *args, **kwargs):
        # توليد الباركود إذا لم يكن موجود
        if not self.barcode:
            date_part = datetime.now().strftime('%y%m%d')
            random_part = str(random.randint(1000, 9999))
            self.barcode = f"{date_part}{random_part}"

        # حساب العمر أو تاريخ الميلاد اعتمادًا على ما تم إدخاله
        if self.date_of_birth and not self.age:
            self.age = self.calculate_age()
        elif self.age and not self.date_of_birth:
            self.date_of_birth = self.estimate_birthdate_from_age()
        elif self.date_of_birth and self.age:
            # تحديث العمر إذا تم تعديل تاريخ الميلاد
            self.age = self.calculate_age()

        super().save(*args, **kwargs)

    # @property
    # def age(self):
    #     """حساب العمر"""
    #     from datetime import date
    #     today = date.today()
    #     return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))



class IndividualTest(models.Model):
    """نموذج التحليل الفردي"""
    DEPARTMENT = [
        ('hematology', 'hematology'),
        ('chemistry', 'chemistry'),
        ('bactrology', 'bactrology'),
        ('imunity', 'imunity'),
        ('histology', 'histology'),
        ('parasitology', 'parasitology'),
    ]
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, verbose_name='اسم التحليل')
    app_name = models.CharField(max_length=100, default="singletest")  # 👈 اضف default
    # description = models.TextField(choices=DEPARTMENT,blank=True, verbose_name='الوصف')
    description =models.CharField(max_length=20, choices=DEPARTMENT, default='hematology', verbose_name='الحالة')
    # subclass = models.TextField(blank=True, verbose_name='subclass')
    subclass = models.CharField(max_length=100, blank=True, verbose_name='subclass')
    unit = models.CharField(max_length=50, verbose_name='الوحدة')
    normal_value_min_m = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='القيمة الطبيعية الدنيا رجال')
    normal_value_max_m = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='القيمة الطبيعية العليا رجال')
    normal_value_min_f = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='القيمة الطبيعية الدنيا نساء')
    normal_value_max_f = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='القيمة الطبيعية العليا نساء')
    normal_value_m = models.TextField(blank=True, null=True, verbose_name='القيم الطبيعية رجال') # يسمح بأن يكون فارغًا في النماذج# يسمح بأن يكون فارغًا في قاعدة البيانات
    normal_value_f = models.TextField(blank=True, null=True, verbose_name='القيم الطبيعية نساء')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name='السعر')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    display_order = models.PositiveIntegerField(default=0, verbose_name="ترتيب العرض")
    
    class Meta:
        verbose_name = 'تحليل فردي'
        verbose_name_plural = 'التحاليل الفردية'
        ordering = ['display_order']
    
    def __str__(self):
        return self.name


class TestGroup(models.Model):
    """نموذج مجموعة التحاليل"""
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, verbose_name='اسم المجموعة')
    app_name = models.CharField(max_length=100, default="paneltest")  # 👈 اضف default
    description = models.TextField(null=True, blank=True, verbose_name='الوصف')
    tests = models.ManyToManyField(IndividualTest, verbose_name='التحاليل المتضمنة')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], verbose_name='السعر الإجمالي')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    
    class Meta:
        verbose_name = 'مجموعة تحاليل'
        verbose_name_plural = 'مجموعات التحاليل'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_individual_price_sum(self):
        """حساب مجموع أسعار التحاليل الفردية"""
        return sum(test.price for test in self.tests.all())


class TestRequest(models.Model):
    """نموذج طلب التحليل"""
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ]
    
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id = models.AutoField(primary_key=True)
    #patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name='المريض')
    patient = models.ForeignKey(Patient,to_field='barcode', on_delete=models.CASCADE, verbose_name='المريض') # ✅ يربط عن طريق حقل barcode بدلاً من id
    individual_tests = models.ManyToManyField(IndividualTest, blank=True, verbose_name='التحاليل الفردية')
    test_groups = models.ManyToManyField(TestGroup, blank=True, verbose_name='مجموعات التحاليل')
    request_date = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الطلب')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='أنشئ بواسطة')
    
    class Meta:
        verbose_name = 'طلب تحليل'
        verbose_name_plural = 'طلبات التحاليل'
        ordering = ['-request_date']
    
    def __str__(self):
        return f"طلب {self.patient.full_name} - {self.request_date.strftime('%Y-%m-%d')}"
    
    def get_total_price(self):
        """حساب السعر الإجمالي للطلب"""
        individual_price = sum(test.price for test in self.individual_tests.all())
        group_price = sum(group.total_price for group in self.test_groups.all())
        return individual_price + group_price
    
    def check_completion_status(self):
        """التحقق من اكتمال جميع النتائج وتحديث الحالة"""
        # التحقق من النتائج الفردية
        individual_tests_count = self.individual_tests.count()
        individual_results_count = IndividualTestResult.objects.filter(test_request=self).count()
        
        # التحقق من نتائج المجموعات
        group_tests_count = 0
        for group in self.test_groups.all():
            group_tests_count += group.tests.count()
        
        group_results_count = TestGroupResult.objects.filter(test_request=self).count()
        
        # إجمالي التحاليل المطلوبة والنتائج المدخلة
        total_tests = individual_tests_count + group_tests_count
        total_results = individual_results_count + group_results_count
        
        # تحديث الحالة إذا تم إدخال جميع النتائج
        if total_tests > 0 and total_results >= total_tests:
            if self.status != 'completed':
                self.status = 'completed'
                self.save(update_fields=['status'])
                return True
        elif total_results > 0 and self.status == 'pending':
            # تحديث إلى "قيد التنفيذ" إذا تم إدخال بعض النتائج
            self.status = 'in_progress'
            self.save(update_fields=['status'])
            return True
        
        return False
    
    def get_completion_percentage(self):
        """حساب نسبة اكتمال النتائج"""
        individual_tests_count = self.individual_tests.count()
        individual_results_count = IndividualTestResult.objects.filter(test_request=self).count()
        
        group_tests_count = 0
        for group in self.test_groups.all():
            group_tests_count += group.tests.count()
        
        group_results_count = TestGroupResult.objects.filter(test_request=self).count()
        
        total_tests = individual_tests_count + group_tests_count
        total_results = individual_results_count + group_results_count
        
        if total_tests == 0:
            return 0
        
        return round((total_results / total_tests) * 100, 1)


# class IndividualTestResult(models.Model):
#     """نموذج نتيجة التحليل الفردي"""
#     STATUS_CHOICES = [
#         ('normal', 'طبيعي'),
#         ('high', 'مرتفع'),
#         ('low', 'منخفض'),
#         ('abnormal', 'غير طبيعي'),
#     ]
    
#     # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     id = models.AutoField(primary_key=True)
#     test_request = models.ForeignKey(TestRequest, on_delete=models.CASCADE, verbose_name='طلب التحليل')
#     individual_test = models.ForeignKey(IndividualTest, on_delete=models.CASCADE, verbose_name='التحليل')
#     # value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='القيمة')
#     value = models.CharField(max_length=100, verbose_name="القيمة")
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES,blank=True, verbose_name='الحالة')
#     result_date = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ النتيجة')
#     notes = models.TextField(blank=True, verbose_name='ملاحظات')
#     entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='أدخل بواسطة')
    
#     class Meta:
#         verbose_name = 'نتيجة تحليل فردي'
#         verbose_name_plural = 'نتائج التحاليل الفردية'
#         ordering = ['-result_date']
#         unique_together = ['test_request', 'individual_test']
    
#     def __str__(self):
#         return f"{self.individual_test.name} - {self.value} {self.individual_test.unit}"
    
#     def save(self, *args, **kwargs):
#         """تحديد حالة النتيجة تلقائياً بناءً على القيم الطبيعية وتحديث حالة الطلب"""
#         if self.individual_test.normal_value_min and self.individual_test.normal_value_max:
#             if self.value < self.individual_test.normal_value_min:
#                 self.status = 'low'
#             elif self.value > self.individual_test.normal_value_max:
#                 self.status = 'high'
#             else:
#                 self.status = 'normal'
        
#         super().save(*args, **kwargs)
        
#         # تحديث حالة طلب التحليل بعد حفظ النتيجة
#         if self.test_request:
#             self.test_request.check_completion_status()

from decimal import Decimal, InvalidOperation

# class IndividualTestResult(models.Model):
#     """نموذج نتيجة التحليل الفردي"""
#     STATUS_CHOICES = [
#         ('normal', 'طبيعي'),
#         ('high', 'مرتفع'),
#         ('low', 'منخفض'),
#         ('abnormal', 'غير طبيعي'),
#         ('n/a', 'غير محدد'),
#     ]
    
#     id = models.AutoField(primary_key=True)
#     test_request = models.ForeignKey(TestRequest, on_delete=models.CASCADE, verbose_name='طلب التحليل')
#     individual_test = models.ForeignKey(IndividualTest, on_delete=models.CASCADE, verbose_name='التحليل')
#     value = models.CharField(max_length=100, verbose_name="القيمة")  # 👈 يدعم أرقام + نصوص
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True, verbose_name='الحالة')
#     result_date = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ النتيجة')
#     notes = models.TextField(blank=True, verbose_name='ملاحظات')
#     # entered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='أدخل بواسطة')
#      # المستخدم الذي أدخل النتيجة أول مرة
#     entered_by = models.ForeignKey(User, related_name="results_entered",on_delete=models.SET_NULL, null=True, blank=True, verbose_name='أدخل بواسطة')
#     # آخر مستخدم عدل النتيجة
#     last_modified_by = models.ForeignKey(User, related_name="results_modified",on_delete=models.SET_NULL, null=True, blank=True, verbose_name='اخر تغديل بواسطة'  )
#     # التاريخ والوقت
#     created_at = models.DateTimeField(auto_now_add=True)   # أول إدخال
#     updated_at = models.DateTimeField(auto_now=True)       # آخر تعديل

#     class Meta:
#         verbose_name = 'نتيجة تحليل فردي'
#         verbose_name_plural = 'نتائج التحاليل الفردية'
#         ordering = ['-result_date']
#         unique_together = ['test_request', 'individual_test']
    
#     def __str__(self):
#         return f"{self.individual_test.name} - {self.value} {self.individual_test.unit}"
    
#     def save(self, *args, **kwargs):
#         """تحديد حالة النتيجة تلقائياً بناءً على القيم الطبيعية وجنس المريض"""
#         try:
#             numeric_value = Decimal(self.value)
            
#             gender = self.test_request.patient.get_gender_display()
            
#             if gender == 'ذكر':
#                 min_val = self.individual_test.normal_value_min_m
#                 max_val = self.individual_test.normal_value_max_m or self.individual_test.normal_value_max
#             else:  # أنثى
#                 min_val = self.individual_test.normal_value_min_f
#                 max_val = self.individual_test.normal_value_max_f or self.individual_test.normal_value_max

#             # تحويل القيم إلى Decimal إذا لم تكن None أو فارغة
#             min_val = Decimal(min_val) if min_val not in [None, ''] else None
#             max_val = Decimal(max_val) if max_val not in [None, ''] else None

#             # تحديد الحالة
#             if min_val is not None and numeric_value < min_val:
#                 self.status = 'low'
#             elif max_val is not None and numeric_value > max_val:
#                 self.status = 'high'
#             else:
#                 self.status = 'normal'

#         except (InvalidOperation, TypeError):
#             # إذا القيمة ليست رقم (مثلاً "Positive" أو "++")
#             if not self.status:
#                 self.status = 'n/a'
        
#         super().save(*args, **kwargs)
        
#         # تحديث حالة طلب التحليل بعد حفظ النتيجة
#         if self.test_request:
#             self.test_request.check_completion_status()
from decimal import Decimal, InvalidOperation
from django.db import models
from django.contrib.auth.models import User
from lab.models import TestRequest, IndividualTest  # تأكد من المسار الصحيح للنماذج

class IndividualTestResult(models.Model):
    """نموذج نتيجة التحليل الفردي"""
    
    STATUS_CHOICES = [
        ('normal', 'طبيعي'),
        ('high', 'مرتفع'),
        ('low', 'منخفض'),
        ('abnormal', 'غير طبيعي'),
        ('n/a', 'غير محدد'),
    ]

    id = models.AutoField(primary_key=True)
    test_request = models.ForeignKey(TestRequest, on_delete=models.CASCADE, verbose_name='طلب التحليل')
    individual_test = models.ForeignKey(IndividualTest, on_delete=models.CASCADE, verbose_name='التحليل')
    value = models.CharField(max_length=100, verbose_name="القيمة")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True, verbose_name='الحالة')
    result_date = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ النتيجة')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')

    entered_by = models.ForeignKey(
        User,
        related_name="results_entered",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='أدخل بواسطة'
    )

    last_modified_by = models.ForeignKey(
        User,
        related_name="results_modified",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='آخر تعديل بواسطة'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'نتيجة تحليل فردي'
        verbose_name_plural = 'نتائج التحاليل الفردية'
        ordering = ['-result_date']
        unique_together = ['test_request', 'individual_test']

    def __str__(self):
        return f"{self.individual_test.name} - {self.value} {self.individual_test.unit}"

    def save(self, *args, **kwargs):
        """تحديد حالة النتيجة تلقائياً بناءً على القيم الطبيعية وجنس المريض"""
        try:
            numeric_value = Decimal(self.value)
            gender = self.test_request.patient.get_gender_display()

            if gender == 'ذكر':
                min_val = self.individual_test.normal_value_min_m
                max_val = self.individual_test.normal_value_max_m
                # إذا كانت القيم الفارغة، استخدم النص العام
                if min_val is None or max_val is None:
                    try:
                        vals = self.individual_test.normal_value_m.split('-')
                        min_val = Decimal(vals[0].strip())
                        max_val = Decimal(vals[1].strip()) if len(vals) > 1 else None
                    except Exception:
                        min_val, max_val = None, None

            else:  # أنثى
                min_val = self.individual_test.normal_value_min_f
                max_val = self.individual_test.normal_value_max_f
                if min_val is None or max_val is None:
                    try:
                        vals = self.individual_test.normal_value_f.split('-')
                        min_val = Decimal(vals[0].strip())
                        max_val = Decimal(vals[1].strip()) if len(vals) > 1 else None
                    except Exception:
                        min_val, max_val = None, None

            # تحديد الحالة
            if min_val is not None and numeric_value < min_val:
                self.status = 'low'
            elif max_val is not None and numeric_value > max_val:
                self.status = 'high'
            else:
                self.status = 'normal'

        except (InvalidOperation, TypeError, AttributeError):
            # إذا القيمة ليست رقمية (مثلاً "Positive") أو لا يمكن استخراج القيم
            if not self.status:
                self.status = 'n/a'

        super().save(*args, **kwargs)

        # تحديث حالة طلب التحليل بعد حفظ النتيجة
        if self.test_request:
            self.test_request.check_completion_status()


class TestGroupResult(models.Model):
    """نموذج نتيجة مجموعة التحاليل"""
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('completed', 'مكتمل'),
    ]
    
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id = models.AutoField(primary_key=True)
    test_request = models.ForeignKey(TestRequest, on_delete=models.CASCADE, verbose_name='طلب التحليل')
    test_group = models.ForeignKey(TestGroup, on_delete=models.CASCADE, verbose_name='مجموعة التحاليل')
    result_date = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ النتيجة')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    class Meta:
        verbose_name = 'نتيجة مجموعة تحاليل'
        verbose_name_plural = 'نتائج مجموعات التحاليل'
        ordering = ['-result_date']
        unique_together = ['test_request', 'test_group']
    
    def __str__(self):
        return f"{self.test_group.name} - {self.test_request.patient.full_name}"


    
    def save(self, *args, **kwargs):
        """تحديث حالة طلب التحليل بعد حفظ نتيجة المجموعة"""
        super().save(*args, **kwargs)
        
        # تحديث حالة طلب التحليل بعد حفظ النتيجة
        if self.test_request:
            self.test_request.check_completion_status()


class PrintedReport(models.Model):
    """نموذج لتتبع التقارير المطبوعة"""
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name='المريض')
    printed_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الطباعة')
    printed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='طبع بواسطة')
    report_type = models.CharField(max_length=50, default='patient_report', verbose_name='نوع التقرير')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    
    class Meta:
        verbose_name = 'تقرير مطبوع'
        verbose_name_plural = 'التقارير المطبوعة'
        ordering = ['-printed_at']
    
    def __str__(self):
        return f"تقرير {self.patient.full_name} - {self.printed_at.strftime('%Y-%m-%d %H:%M')}"




from django.db import models
from django.utils import timezone

class DeviceResult(models.Model):
    device_name = models.CharField(max_length=200, verbose_name="اسم الجهاز")
    barcode = models.ForeignKey(
        'Patient',
        to_field='barcode',
        on_delete=models.CASCADE,
        verbose_name='المريض'
    )
    test = models.ForeignKey(
        'IndividualTest',
        on_delete=models.CASCADE,
        verbose_name='التحليل'
    )
    result = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="نتيجة التحليل")
    insert_datetime = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ النتيجة')
    is_active = models.BooleanField(default=True, verbose_name="نشط")  # للتحكم بالنتائج النشطة

    class Meta:
        verbose_name = "نتيجة جهاز"
        verbose_name_plural = "نتائج الأجهزة"
        ordering = ["-insert_datetime"]
        constraints = [
            # يسمح بإدخالات متكررة لكل جهاز/مريض/تحليل لكن كل إدخال له وقت مختلف
            models.UniqueConstraint(
                fields=['barcode', 'test', 'insert_datetime'],
                name='unique_device_barcode_test_time'
            )
        ]

    def __str__(self):
        return f"{self.device_name} - {self.barcode.barcode} - {self.test.name} - {self.result} - {'نشط' if self.is_active else 'غير نشط'}"

