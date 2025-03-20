from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.urls import reverse

def send_verification_email(user):
    """Отправляет письмо с подтверждением email"""
    try:
        verification_link = settings.SITE_URL + reverse('verify-email', args=[str(user.verification_token)])

        subject = "Подтверждение email на сайте мероприятий"
        text_content = f"Привет, {user.username}!\n\nДля подтверждения email перейдите по ссылке:\n{verification_link}\n\nСпасибо!"
        html_content = f"""
            <html>
                <body>
                    <p>Привет, {user.username}!</p>
                    <p>Для подтверждения email перейдите по ссылке:</p>
                    <p><a href="{verification_link}">{verification_link}</a></p>
                    <p>Спасибо!</p>
                </body>
            </html>
        """

        print(f"[DEBUG] Отправляется письмо на {user.email}")
        print(f"[DEBUG] Ссылка подтверждения: {verification_link}")

        msg = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [user.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        print("[SUCCESS] Письмо успешно отправлено!")

    except Exception as e:
        print(f"[ERROR] Ошибка отправки email: {e}")
