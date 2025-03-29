from django import template
from users.utils import generate_qr_code_base64_for_task

register = template.Library()


@register.filter
def generate_task_qr(task):
    return generate_qr_code_base64_for_task(task)
