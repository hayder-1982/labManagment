from django import forms
from django.forms import formset_factory
from .models import Patient, TestRequest, IndividualTest, TestGroup, IndividualTestResult, TestGroupResult

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['full_name', 'date_of_birth','age', 'gender', 'phone_number', 'address']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'الاسم الكامل'}),
            # 'national_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الهوية'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'العمر'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'رقم الهاتف'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'العنوان'}),
        }

class TestRequestForm(forms.ModelForm):
    class Meta:
        model = TestRequest
        fields = ['patient', 'individual_tests', 'test_groups', 'notes']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-select'}),
            'individual_tests': forms.CheckboxSelectMultiple(),
            'test_groups': forms.CheckboxSelectMultiple(),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'ملاحظات إضافية'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['individual_tests'].queryset = IndividualTest.objects.filter(is_active=True)
        self.fields['test_groups'].queryset = TestGroup.objects.filter(is_active=True)

class IndividualTestResultForm(forms.ModelForm):
    class Meta:
        model = IndividualTestResult
        fields = ['value', 'notes']
        widgets = {
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'القيمة'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'ملاحظات'}),
        }

class BulkIndividualTestResultForm(forms.Form):
    """نموذج لإدخال نتائج التحاليل الفردية دفعة واحدة"""
    
    def __init__(self, test_request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_request = test_request
        
        # جلب جميع التحاليل الفردية المرتبطة بطلب التحليل
        individual_tests = test_request.individual_tests.all()
        
        # جلب النتائج الموجودة مسبقاً
        existing_results = {
            result.individual_test.id: result 
            for result in IndividualTestResult.objects.filter(test_request=test_request)
        }
        
        # إنشاء حقول لكل تحليل فردي
        for test in individual_tests:
            existing_result = existing_results.get(test.id)
            
            # حقل القيمة
            value_field_name = f'test_{test.id}_value'
            self.fields[value_field_name] = forms.DecimalField(
                label=f'{test.name} ({test.unit})',
                max_digits=10,
                decimal_places=2,
                required=False,
                initial=existing_result.value if existing_result else None,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'placeholder': f'القيمة ({test.unit})'
                })
            )
            
            # حقل الملاحظات
            notes_field_name = f'test_{test.id}_notes'
            self.fields[notes_field_name] = forms.CharField(
                label=f'ملاحظات {test.name}',
                required=False,
                initial=existing_result.notes if existing_result else '',
                widget=forms.Textarea(attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': 'ملاحظات إضافية'
                })
            )
            
            # إضافة معلومات التحليل كخصائص للنموذج
            setattr(self, f'test_{test.id}_info', {
                'test': test,
                'existing_result': existing_result,
                'value_field': value_field_name,
                'notes_field': notes_field_name
            })
    
    def get_test_fields(self):
        """إرجاع قائمة بمعلومات التحاليل والحقول المرتبطة بها"""
        test_fields = []
        for test in self.test_request.individual_tests.all():
            test_info = getattr(self, f'test_{test.id}_info', None)
            if test_info:
                test_fields.append({
                    'test': test,
                    'value_field': self[test_info['value_field']],
                    'notes_field': self[test_info['notes_field']],
                    'existing_result': test_info['existing_result']
                })
        return test_fields
    
    def save(self, user):
        """حفظ نتائج التحاليل"""
        saved_results = []
        
        for test in self.test_request.individual_tests.all():
            value_field_name = f'test_{test.id}_value'
            notes_field_name = f'test_{test.id}_notes'
            
            value = self.cleaned_data.get(value_field_name)
            notes = self.cleaned_data.get(notes_field_name, '')
            
            # تخطي التحاليل التي لم يتم إدخال قيمة لها
            if value is None:
                continue
            
            # البحث عن النتيجة الموجودة أو إنشاء جديدة
            result, created = IndividualTestResult.objects.get_or_create(
                test_request=self.test_request,
                individual_test=test,
                defaults={
                    'value': value,
                    'notes': notes,
                    'entered_by': user
                }
            )
            
            # تحديث النتيجة إذا كانت موجودة مسبقاً
            if not created:
                result.value = value
                result.notes = notes
                result.entered_by = user
                result.save()
            
            saved_results.append(result)
        
        return saved_results

class BulkTestGroupResultForm(forms.Form):
    """نموذج لإدخال نتائج مجموعات التحاليل دفعة واحدة"""
    
    def __init__(self, test_request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_request = test_request
        
        # جلب جميع مجموعات التحاليل المرتبطة بطلب التحليل
        test_groups = test_request.test_groups.all()
        
        # جلب النتائج الموجودة مسبقاً للتحاليل الفردية
        existing_individual_results = {
            result.individual_test.id: result 
            for result in IndividualTestResult.objects.filter(test_request=test_request)
        }
        
        # إنشاء حقول لكل تحليل في كل مجموعة
        for group in test_groups:
            for test in group.tests.all():
                existing_result = existing_individual_results.get(test.id)
                
                # حقل القيمة
                value_field_name = f'group_{group.id}_test_{test.id}_value'
                self.fields[value_field_name] = forms.DecimalField(
                    label=f'{test.name} ({test.unit}) - {group.name}',
                    max_digits=10,
                    decimal_places=2,
                    required=False,
                    initial=existing_result.value if existing_result else None,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'step': '0.01',
                        'placeholder': f'القيمة ({test.unit})'
                    })
                )
                
                # حقل الملاحظات
                notes_field_name = f'group_{group.id}_test_{test.id}_notes'
                self.fields[notes_field_name] = forms.CharField(
                    label=f'ملاحظات {test.name} - {group.name}',
                    required=False,
                    initial=existing_result.notes if existing_result else '',
                    widget=forms.Textarea(attrs={
                        'class': 'form-control',
                        'rows': 2,
                        'placeholder': 'ملاحظات إضافية'
                    })
                )
                
                # إضافة معلومات التحليل كخصائص للنموذج
                setattr(self, f'group_{group.id}_test_{test.id}_info', {
                    'group': group,
                    'test': test,
                    'existing_result': existing_result,
                    'value_field': value_field_name,
                    'notes_field': notes_field_name
                })
    
    def get_group_fields(self):
        """إرجاع قائمة بمعلومات مجموعات التحاليل والحقول المرتبطة بها"""
        group_fields = []
        for group in self.test_request.test_groups.all():
            tests_in_group = []
            for test in group.tests.all():
                test_info = getattr(self, f'group_{group.id}_test_{test.id}_info', None)
                if test_info:
                    tests_in_group.append({
                        'test': test,
                        'value_field': self[test_info['value_field']],
                        'notes_field': self[test_info['notes_field']],
                        'existing_result': test_info['existing_result']
                    })
            
            if tests_in_group:
                group_fields.append({
                    'group': group,
                    'tests': tests_in_group
                })
        
        return group_fields
    
    def save(self, user):
        """حفظ نتائج مجموعات التحاليل"""
        saved_results = []
        
        for group in self.test_request.test_groups.all():
            for test in group.tests.all():
                value_field_name = f'group_{group.id}_test_{test.id}_value'
                notes_field_name = f'group_{group.id}_test_{test.id}_notes'
                
                value = self.cleaned_data.get(value_field_name)
                notes = self.cleaned_data.get(notes_field_name, '')
                
                # تخطي التحاليل التي لم يتم إدخال قيمة لها
                if value is None:
                    continue
                
                # البحث عن النتيجة الموجودة أو إنشاء جديدة
                result, created = IndividualTestResult.objects.get_or_create(
                    test_request=self.test_request,
                    individual_test=test,
                    defaults={
                        'value': value,
                        'notes': notes,
                        'entered_by': user
                    }
                )
                
                # تحديث النتيجة إذا كانت موجودة مسبقاً
                if not created:
                    result.value = value
                    result.notes = notes
                    result.entered_by = user
                    result.save()
                
                saved_results.append(result)
        
        return saved_results

