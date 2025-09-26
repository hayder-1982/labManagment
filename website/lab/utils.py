import pdfkit
import pywhatkit
from django.shortcuts import get_object_or_404
from .models import Patient, TestRequest, IndividualTestResult, TestGroupResult
from django.utils import timezone
from django.template.loader import render_to_string

def send_patient_report_whatsapp(patient_id, phone_number):
    # جلب بيانات المريض
    patient = get_object_or_404(Patient, id=patient_id)

    test_requests = TestRequest.objects.filter(patient=patient).order_by('-request_date')
    individual_results = IndividualTestResult.objects.filter(test_request__patient=patient).select_related('individual_test', 'test_request').order_by('-result_date')
    group_results = TestGroupResult.objects.filter(test_request__patient=patient).select_related('test_group', 'test_request').order_by('-result_date')

    # تنظيم النتائج حسب الوصف
    results_by_description = {}
    for result in individual_results:
        test = result.individual_test
        group_key = test.subclass.strip() if test.subclass else test.description.strip() if test.description else test.name
        normal_min, normal_max = ('', '')
        if patient.gender == "M":
            normal_min = test.normal_value_min_m or test.normal_value_m or ''
            normal_max = test.normal_value_max_m or ''
        else:
            normal_min = test.normal_value_min_f or ''
            normal_max = test.normal_value_max_f or test.normal_value_f or ''

        if group_key not in results_by_description:
            results_by_description[group_key] = []

        results_by_description[group_key].append({
            'test_name': test.name,
            'result_value': result.value,
            'unit': test.unit,
            'normal_range': f"{normal_min} - {normal_max}".strip(' -'),
            'status': result.status,
            'result_date': result.result_date,
            'test_request': result.test_request,
        })

    for result in group_results:
        group_key = result.test_group.description.strip() if result.test_group.description else result.test_group.name
        if group_key not in results_by_description:
            results_by_description[group_key] = []
        results_by_description[group_key].append({
            'test_name': result.test_group.name,
            'result_value': 'مجموعة تحاليل',
            'unit': '',
            'normal_range': '',
            'status': result.status,
            'result_date': result.result_date,
            'test_request': result.test_request,
        })

    # تحويل HTML إلى string
    html_string = render_to_string('lab/patient_report_print.html', {
        'patient': patient,
        'results_by_group': results_by_description,
        'report_date': timezone.now(),
    })

    # حفظ PDF
    pdf_file_path = f'reports/{patient.full_name}_report.pdf'
    pdfkit.from_string(html_string, pdf_file_path)

    # إرسال عبر واتساب
    # رقم الهاتف يجب أن يكون بالشكل الدولي: 964xxxxxxxxx
    pywhatkit.sendwhats_image(phone_number, pdf_file_path, caption=f"تقرير نتائج التحاليل الطبية للمريض {patient.full_name}")

    return pdf_file_path


