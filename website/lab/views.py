from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Patient, IndividualTest, TestGroup, TestRequest, IndividualTestResult, TestGroupResult
from .forms import PatientForm, TestRequestForm, IndividualTestResultForm, BulkIndividualTestResultForm, BulkTestGroupResultForm

def home(request):
    """الصفحة الرئيسية"""
    # إحصائيات سريعة
    total_patients = Patient.objects.count()
    total_requests = TestRequest.objects.count()
    pending_requests = TestRequest.objects.filter(status='pending').count()
    completed_requests = TestRequest.objects.filter(status='completed').count()
    
    # آخر الطلبات
    recent_requests = TestRequest.objects.select_related('patient').order_by('-request_date')[:5]
    
    context = {
        'total_patients': total_patients,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'completed_requests': completed_requests,
        'recent_requests': recent_requests,
    }
    return render(request, 'lab/home.html', context)

@login_required
def patient_list(request):
    """قائمة المرضى"""
    search_query = request.GET.get('search', '')
    patients = Patient.objects.all()
    
    if search_query:
        patients = patients.filter(
            Q(full_name__icontains=search_query) |
            # Q(national_id__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )
    
    paginator = Paginator(patients, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'lab/patient_list.html', context)

@login_required
def patient_detail(request, patient_id):
    """تفاصيل المريض"""
    patient = get_object_or_404(Patient, id=patient_id)
    test_requests = TestRequest.objects.filter(patient=patient).order_by('-request_date')
    
    context = {
        'patient': patient,
        'test_requests': test_requests,
    }
    return render(request, 'lab/patient_detail.html', context)

@login_required
def patient_create(request):
    """إضافة مريض جديد"""
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save()
            messages.success(request, f'تم إضافة المريض {patient.full_name} بنجاح')
            # return redirect('patient_detail', patient_id=patient.id)
            return redirect(reverse('test_request_create_with_patient', kwargs={'patient_id': patient.id}))
    else:
        form = PatientForm()
    
    context = {'form': form}
    return render(request, 'lab/patient_form.html', context)

@login_required
def patient_edit(request, patient_id):
    """تعديل بيانات المريض"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f'تم تحديث بيانات المريض {patient.full_name} بنجاح')
            return redirect('patient_detail', patient_id=patient.id)
    else:
        form = PatientForm(instance=patient)
    
    context = {'form': form, 'patient': patient}
    return render(request, 'lab/patient_form.html', context)

@login_required
def test_list(request):
    """قائمة التحاليل"""
    individual_tests = IndividualTest.objects.filter(is_active=True).order_by('name')
    test_groups = TestGroup.objects.filter(is_active=True).order_by('name')
    
    context = {
        'individual_tests': individual_tests,
        'test_groups': test_groups,
    }
    return render(request, 'lab/test_list.html', context)

@login_required
def test_request_list(request):
    """قائمة طلبات التحاليل"""
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    requests = TestRequest.objects.select_related('patient').all()
    
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    if search_query:
        requests = requests.filter(
            Q(patient__full_name__icontains=search_query) |
            Q(patient__barcode__icontains=search_query)
        )
    
    requests = requests.order_by('-request_date')
    
    paginator = Paginator(requests, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': TestRequest.STATUS_CHOICES,
    }
    return render(request, 'lab/test_request_list.html', context)

@login_required
def test_request_detail(request, request_id):
    """تفاصيل طلب التحليل"""
    test_request = get_object_or_404(TestRequest, id=request_id)
    
    # جلب نتائج التحاليل الفردية المرتبطة بطلب التحليل
    individual_results = {str(result.individual_test.id): result for result in IndividualTestResult.objects.filter(test_request=test_request)}
    
    context = {
        'test_request': test_request,
        'individual_results': individual_results,
    }
    return render(request, 'lab/test_request_detail.html', context)

@login_required
def test_request_create(request, patient_id=None):
    """إنشاء طلب تحليل جديد"""
    selected_patient = None
    if patient_id:
        selected_patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        form = TestRequestForm(request.POST)
        if form.is_valid():
            test_request = form.save(commit=False)
            test_request.created_by = request.user
            test_request.save()
            form.save_m2m()  # حفظ العلاقات many-to-many
            
            messages.success(request, 'تم إنشاء طلب التحليل بنجاح')
            return redirect('test_request_detail', request_id=test_request.id)
    else:
        initial_data = {}
        if selected_patient:
            initial_data['patient'] = selected_patient
        form = TestRequestForm(initial=initial_data)
    form.fields['individual_tests'].queryset = IndividualTest.objects.all().order_by('description', 'name')
    
    context = {
        'form': form,
        'selected_patient': selected_patient,
        'is_edit': False,
    }
    return render(request, 'lab/test_request_form.html', context)

@login_required
def add_test_result(request, request_id, test_id):
    """إضافة نتيجة تحليل فردي"""
    test_request = get_object_or_404(TestRequest, id=request_id)
    individual_test = get_object_or_404(IndividualTest, id=test_id)
    
    # التحقق من وجود النتيجة مسبقاً
    existing_result = IndividualTestResult.objects.filter(
        test_request=test_request,
        individual_test=individual_test
    ).first()
    
    if request.method == 'POST':
        form = IndividualTestResultForm(request.POST, instance=existing_result)
        if form.is_valid():
            result = form.save(commit=False)
            result.test_request = test_request
            result.individual_test = individual_test
            result.entered_by = request.user
            result.save()
            
            messages.success(request, f'تم حفظ نتيجة تحليل {individual_test.name} بنجاح')
            return redirect('test_request_detail', request_id=test_request.id)
    else:
        form = IndividualTestResultForm(instance=existing_result)
    
    context = {
        'form': form,
        'test_request': test_request,
        'individual_test': individual_test,
        'existing_result': existing_result,
    }
    return render(request, 'lab/test_result_form.html', context)

@login_required
def search_patients_ajax(request):
    """البحث عن المرضى عبر AJAX"""
    query = request.GET.get('q', '')
    patients = []
    
    if query:
        patient_objects = Patient.objects.filter(
            Q(full_name__icontains=query) 
            # Q(national_id__icontains=query)
        )[:10]
        
        patients = [
            {
                'id': str(patient.id),
                'text': f'{patient.full_name} - {patient.barcode}'
            }
            for patient in patient_objects
        ]
    
    return JsonResponse({'results': patients})

@login_required
def reports(request):
    """صفحة التقارير"""
    # إحصائيات عامة
    total_patients = Patient.objects.count()
    total_requests = TestRequest.objects.count()
    
    # إحصائيات حسب الحالة
    status_stats = TestRequest.objects.values('status').annotate(count=Count('id'))
    
    # أكثر التحاليل طلباً
    popular_tests = IndividualTest.objects.annotate(
        request_count=Count('testrequest')
    ).order_by('-request_count')[:10]
    
    context = {
        'total_patients': total_patients,
        'total_requests': total_requests,
        'status_stats': status_stats,
        'popular_tests': popular_tests,
    }
    return render(request, 'lab/reports.html', context)



@login_required
def test_request_update(request, request_id):
    """تعديل طلب تحليل"""
    test_request = get_object_or_404(TestRequest, id=request_id)
    if request.method == 'POST':
        form = TestRequestForm(request.POST, instance=test_request)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث طلب التحليل بنجاح')
            return redirect('test_request_detail', request_id=test_request.id)
    else:
        form = TestRequestForm(instance=test_request)
        # # جعل حقل المريض غير قابل للتغيير في وضع التعديل
        # form.fields['patient'].disabled = True
    form.fields['individual_tests'].queryset = IndividualTest.objects.all().order_by('description', 'name')
    context = {
        'form': form, 
        'test_request': test_request,
        # 'is_edit': True,
        'selected_patient': test_request.patient,
    }
    return render(request, 'lab/test_request_form.html', context)

@login_required
def test_request_delete(request, request_id):
    """حذف طلب تحليل"""
    test_request = get_object_or_404(TestRequest, id=request_id)
    if request.method == 'POST':
        test_request.delete()
        messages.success(request, 'تم حذف طلب التحليل بنجاح')
        return redirect('test_request_list')
    context = {'test_request': test_request}
    return render(request, 'lab/test_request_confirm_delete.html', context)


@login_required
def bulk_individual_results(request, request_id):
    """إدخال نتائج التحاليل الفردية دفعة واحدة"""
    test_request = get_object_or_404(TestRequest, id=request_id)
    
    if request.method == 'POST':
        form = BulkIndividualTestResultForm(test_request, request.POST)
        if form.is_valid():
            saved_results = form.save(request.user)
            messages.success(request, f'تم حفظ نتائج {len(saved_results)} تحليل بنجاح')
            return redirect('test_request_detail', request_id=test_request.id)
    else:
        form = BulkIndividualTestResultForm(test_request)
    
    context = {
        'form': form,
        'test_request': test_request,
    }
    return render(request, 'lab/bulk_individual_results.html', context)

@login_required
def bulk_group_results(request, request_id):
    """إدخال نتائج مجموعات التحاليل دفعة واحدة"""
    test_request = get_object_or_404(TestRequest, id=request_id)
    
    if request.method == 'POST':
        form = BulkTestGroupResultForm(test_request, request.POST)
        if form.is_valid():
            saved_results = form.save(request.user)
            messages.success(request, f'تم حفظ نتائج {len(saved_results)} تحليل بنجاح')
            return redirect('test_request_detail', request_id=test_request.id)
    else:
        form = BulkTestGroupResultForm(test_request)
    
    context = {
        'form': form,
        'test_request': test_request,
    }
    return render(request, 'lab/bulk_group_results.html', context)



@login_required
def patient_report(request, patient_id):
    """تقرير نتائج المريض"""
    patient = get_object_or_404(Patient, id=patient_id)
    
    # جلب جميع طلبات التحاليل للمريض
    test_requests = TestRequest.objects.filter(patient=patient).order_by('-request_date')
    
    # جلب جميع النتائج الفردية للمريض
    individual_results = IndividualTestResult.objects.filter(
        test_request__patient=patient
    ).select_related('individual_test', 'test_request').order_by('-result_date')
    
    # جلب جميع نتائج المجموعات للمريض
    group_results = TestGroupResult.objects.filter(
        test_request__patient=patient
    ).select_related('test_group', 'test_request').order_by('-result_date')
    
    # تنظيم النتائج حسب الوصف (description)
    results_by_description = {}
    
    # إضافة النتائج الفردية
    for result in individual_results:
        # استخدام الوصف كمفتاح التجميع، أو اسم التحليل إذا لم يكن هناك وصف
        group_key = result.individual_test.description.strip() if result.individual_test.description.strip() else result.individual_test.name
        
        if group_key not in results_by_description:
            results_by_description[group_key] = []
        results_by_description[group_key].append({
            'test_name': result.individual_test.name,
            'result_value': result.value,
            'unit': result.individual_test.unit,
            'normal_range': f"{result.individual_test.normal_value_min or ''} - {result.individual_test.normal_value_max or ''}".strip(' -'),
            'status': result.status,
            'result_date': result.result_date,
            'test_request': result.test_request,
        })
    
    # إضافة نتائج المجموعات
    for result in group_results:
        group_key = result.test_group.description.strip() if result.test_group.description.strip() else result.test_group.name
        
        if group_key not in results_by_description:
            results_by_description[group_key] = []
        # نحتاج إلى جلب النتائج الفردية لهذه المجموعة
        # لأن TestGroupResult لا يحتوي على نتائج فردية مباشرة
        # سنعرض معلومات المجموعة فقط
        results_by_description[group_key].append({
            'test_name': result.test_group.name,
            'result_value': 'مجموعة تحاليل',
            'unit': '',
            'normal_range': '',
            'status': result.status,
            'result_date': result.result_date,
            'test_request': result.test_request,
        })
    
    context = {
        'patient': patient,
        'test_requests': test_requests,
        'results_by_group': results_by_description,
        'report_date': timezone.now(),
    }
    
    return render(request, 'lab/patient_report.html', context)

@login_required
def patient_report_print(request, patient_id):
    """تقرير نتائج المريض للطباعة"""
    from .models import PrintedReport
    
    patient = get_object_or_404(Patient, id=patient_id)
    
    # تسجيل الطباعة
    PrintedReport.objects.create(
        patient=patient,
        printed_by=request.user,
        report_type='patient_report'
    )
    
    # جلب جميع طلبات التحاليل للمريض
    test_requests = TestRequest.objects.filter(patient=patient).order_by('-request_date')
    
    # جلب جميع النتائج الفردية للمريض
    individual_results = IndividualTestResult.objects.filter(
        test_request__patient=patient
    ).select_related('individual_test', 'test_request').order_by('-result_date')
    print('individual_results',individual_results)
    # جلب جميع نتائج المجموعات للمريض
    group_results = TestGroupResult.objects.filter(
        test_request__patient=patient
    ).select_related('test_group', 'test_request').order_by('-result_date')
    print('group_results',group_results)
    # تنظيم النتائج حسب الوصف (description)
    results_by_description = {}
    
    # إضافة النتائج الفردية
    for result in individual_results:
        # استخدام الوصف كمفتاح التجميع، أو اسم التحليل إذا لم يكن هناك وصف
        group_key = result.individual_test.description.strip() if result.individual_test.description.strip() else result.individual_test.name
        if group_key not in results_by_description:
            results_by_description[group_key] = []
        results_by_description[group_key].append({
            'test_name': result.individual_test.name,
            'result_value': result.value,
            'unit': result.individual_test.unit,
            'normal_range': f"{result.individual_test.normal_value_min or ''} - {result.individual_test.normal_value_max or ''}".strip(' -'),
            'status': result.status,
            'result_date': result.result_date,
            'test_request': result.test_request,
        })
    
    # إضافة نتائج المجموعات
    for result in group_results:
        group_key = result.test_group.description.strip() if result.test_group.description.strip() else result.test_group.name
        print('---------',group_key)
        if group_key not in results_by_description:
            results_by_description[group_key] = []
        # نحتاج إلى جلب النتائج الفردية لهذه المجموعة
        # لأن TestGroupResult لا يحتوي على نتائج فردية مباشرة
        # سنعرض معلومات المجموعة فقط
        results_by_description[group_key].append({
            'test_name': result.test_group.name,
            'result_value': 'مجموعة تحاليل',
            'unit': '',
            'normal_range': '',
            'status': result.status,
            'result_date': result.result_date,
            'test_request': result.test_request,
        })
    
    context = {
        'patient': patient,
        'test_requests': test_requests,
        'results_by_group': results_by_description,
        'report_date': timezone.now(),
    }
    
    return render(request, 'lab/patient_report_print.html', context)


# ----------------------------
import qrcode
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
import json
from django.utils import timezone

import base64
from io import BytesIO
import barcode
from barcode.writer import ImageWriter

import barcode
from barcode.writer import SVGWriter
from io import BytesIO
import base64


@login_required
def patient_barcode_label(request, patient_id):
    """عرض ملصق الباركود للمريض"""
    patient = get_object_or_404(Patient, id=patient_id)
    latest_request = TestRequest.objects.filter(patient=patient).order_by('-request_date').first()
    label_data = generate_patient_barcode_label_data(patient, latest_request)
    
    context = {
        'patient': patient,
        'label_data': label_data,
        'latest_request': latest_request,
    }
    
    return render(request, 'lab/patient_barcode_label.html', context)



@login_required
def patient_barcode_label_print(request, patient_id):
    """طباعة ملصق الباركود للمريض"""
    patient = get_object_or_404(Patient, id=patient_id)
    latest_request = TestRequest.objects.filter(patient=patient).order_by('-request_date').first()
    label_data = generate_patient_barcode_label_data(patient, latest_request)
    
    context = {
        'patient': patient,
        'label_data': label_data,
        'latest_request': latest_request,
    }
    
    return render(request, 'lab/patient_barcode_label_print.html', context)

@login_required
def test_request_barcode_label(request, request_id):
    """ملصق باركود لطلب تحليل محدد"""
    test_request = get_object_or_404(TestRequest, id=request_id)
    label_data = generate_patient_barcode_label_data(test_request.patient, test_request)
    
    context = {
        'patient': test_request.patient,
        'test_request': test_request,
        'label_data': label_data,
    }
    
    return render(request, 'lab/patient_barcode_label.html', context)

@login_required
def test_request_barcode_label_print(request, request_id):
    """طباعة ملصق باركود لطلب تحليل محدد"""
    test_request = get_object_or_404(TestRequest, id=request_id)
    label_data = generate_patient_barcode_label_data(test_request.patient, test_request)
    
    context = {
        'patient': test_request.patient,
        'test_request': test_request,
        'label_data': label_data,
    }
    
    return render(request, 'lab/patient_barcode_label_print.html', context)


# -------------------------------------qr
# في ملف utils.py أو في views.py

def generate_patient_qr_code(patient_data):
    """توليد QR Code للمريض"""
    # print('----------',patient_data)
    qr_data = {
        'patient_id': str(patient_data['id']),
        'name': patient_data['full_name'],
        'barcode': patient_data['barcode'],
        'phone': patient_data['phone_number'],
        'type': 'PATIENT'
    }
    
    qr_content = json.dumps(qr_data, ensure_ascii=False)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_content)
    qr.make(fit=True)
    
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    qr_image.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return qr_base64


def generate_barcode_128(text, scale=2):
    """توليد باركود خطي Code128 بدون نص أسفل"""
    try:
        # code128 = barcode.get_barcode_class('code128')
        # code = code128(text, writer=ImageWriter())
        # buffer = BytesIO()
        # code.write(buffer, options={"write_text": False})  # 🚀 تعطيل النص
        # barcode_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        """توليد باركود Code128 بصيغة SVG عالية الوضوح"""
        code128 = barcode.get("code128", text, writer=SVGWriter())

    # إعدادات الكتابة
        options = {
            "module_width": 0.3 * scale,    # عرض كل خط
            "module_height": 17 * scale,    # ارتفاع الباركود
            "font_size": 10 * scale,        # حجم النص أسفل الباركود
            "text_distance": 3 * scale,     # المسافة بين الباركود والنص
            "quiet_zone": 2 * scale,        # الهامش حول الباركود
            "write_text": False  # أهم شيء: إزالة النص أسفل الباركود
        }

        buffer = BytesIO()
        code128.write(buffer, options)
        barcode_base64 = buffer.getvalue().decode("utf-8")
        return barcode_base64

    except Exception as e:
        print(f"خطأ في توليد الباركود: {e}")
        return None

def generate_patient_barcode_label_data(patient, test_request=None):
    """تحضير بيانات ملصق الباركود"""
    patient_data = {
        'id': patient.id,
        'full_name': patient.full_name,
        'barcode': patient.barcode,
        'phone_number': patient.phone_number,
        'age': patient.age,
        'gender_display': patient.get_gender_display(),
        'created_at': patient.created_at.strftime('%Y-%m-%d')
    }
    
    qr_code = generate_patient_qr_code(patient_data)
    linear_barcode = generate_barcode_128(patient.barcode)
    
    test_info = None
    if test_request:
        individual_tests = list(test_request.individual_tests.values_list('app_name', flat=True))
        test_groups = list(test_request.test_groups.values_list('name', flat=True))
        test_info = {
            'request_id': str(test_request.id),
            'request_date': test_request.request_date.strftime('%Y-%m-%d %H:%M'),
            'status': test_request.get_status_display(),
            'individual_tests': individual_tests,
            'test_groups': test_groups,
            'notes': test_request.notes or ''
        }
    
    return {
        'patient': patient_data,
        'qr_code': qr_code,
        'linear_barcode': linear_barcode,
        'test_info': test_info,
        'generated_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    }

