from django import template

register = template.Library()

@register.filter
def get_item_by_test_id(results_dict, test_id):
    """
    فلتر مخصص للحصول على نتيجة تحليل معين من قاموس النتائج
    """
    return results_dict.get(str(test_id))

@register.filter
def multiply(value, arg):
    """
    فلتر مخصص لضرب قيمتين
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """
    فلتر مخصص لطرح قيمتين
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

