from django.urls import path
from . import views

urlpatterns = [
    # الصفحة الرئيسية
    path("", views.home, name="home"),
    
    # المرضى
    path("patients/", views.patient_list, name="patient_list"),
    path("patients/create/", views.patient_create, name="patient_create"),
    path('requests/create/<patient_id>/', views.test_request_create, name='test_request_create_with_patient'),
    path("patients/<patient_id>/", views.patient_detail, name="patient_detail"),
    path("patients/<patient_id>/edit/", views.patient_edit, name="patient_edit"),
    path("patients/<int:patient_id>/requests/<int:request_id>/tests/<int:test_id>/delete/",views.delete_individual_test,name="delete_individual_test",),
   # حذف تحليل فردي
    # حذف مجموعة تحاليل
    path("patients/<int:patient_id>/requests/<int:request_id>/groups/<int:group_id>/delete/",views.delete_test_group,name="delete_test_group",),
    # التحاليل
    path("tests/", views.test_list, name="test_list"),
    
    # طلبات التحاليل
    path("requests/", views.test_request_list, name="test_request_list"),
    path("requests/create/", views.test_request_create, name="test_request_create"),
    path("requests/create/<patient_id>/", views.test_request_create, name="test_request_create_for_patient"),
    path("requests/<request_id>/", views.test_request_detail, name="test_request_detail"),
    path("requests/<request_id>/results/<test_id>/", views.add_test_result, name="add_test_result"),
    path("requests/<request_id>/bulk-individual-results/", views.bulk_individual_results, name="bulk_individual_results"),
    path("requests/<request_id>/bulk-group-results/", views.bulk_group_results, name="bulk_group_results"),
    path("requests/<request_id>/update/", views.test_request_update, name="test_request_update"),
    path("requests/<request_id>/delete/", views.test_request_delete, name="test_request_delete"),
     # حذف نتيجة تحليل فردي فقط
    path("patients/<int:patient_id>/requests/<int:request_id>/tests/<int:test_id>/delete_result/",views.delete_individual_test_result,name="delete_individual_test_result",),

    # حذف نتائج مجموعة فقط
    path("patients/<int:patient_id>/requests/<int:request_id>/groups/<int:group_id>/delete_results/",views.delete_test_group_results,name="delete_test_group_results",),
    
    # التقارير
    path("reports/", views.reports, name="reports"),
    path("patients/<patient_id>/report/", views.patient_report, name="patient_report"),
    path("patients/<patient_id>/report/print/", views.patient_report_print, name="patient_report_print"),
    
    # ملصقات الباركود
    path("patients/<patient_id>/barcode-label/", views.patient_barcode_label, name="patient_barcode_label"),
    path("patients/<patient_id>/barcode-label/print/", views.patient_barcode_label_print, name="patient_barcode_label_print"),
    path("requests/<request_id>/barcode-label/", views.test_request_barcode_label, name="test_request_barcode_label"),
    path("requests/<request_id>/barcode-label/print/", views.test_request_barcode_label_print, name="test_request_barcode_label_print"),


    # AJAX
    path("ajax/search-patients/", views.search_patients_ajax, name="search_patients_ajax"),


    path('update-device-results/', views.update_device_results, name='update_device_results'),
     
     #واتساب
      
     path('report/pdf/<patient_id>/', views.generate_report_pdf, name='generate_report_pdf'),
     path('report/send-whatsapp/<int:patient_id>/', views.send_report_whatsapp, name='send_report_whatsapp'),

    
]


