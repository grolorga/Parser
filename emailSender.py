import smtplib
from email.mime.text import MIMEText


def send_email(sender_email, sender_password, recipient_email, subject,  body):
    message = MIMEText(f"body")
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject

    s = smtplib.SMTP('smtp.yandex.ru', 587, timeout=10)
    try:
        s.starttls()
        s.login(sender_email, sender_password)
        s.sendmail(message['From'], recipient_email, message.as_string())
    except Exception as e:
        print(e)
    finally:
        s.quit()


# Пример использования
sender_email = ""
sender_password = ""
recipient_email = ""
subject = "Привет из Python!"
body = "Это тестовое письмо, отправленное с помощью Python."

send_email(sender_email, sender_password, recipient_email, subject, body)



