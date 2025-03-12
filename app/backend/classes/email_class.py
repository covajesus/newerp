import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailClass:
    def __init__(self, sender_email: str = "info@jisparking.com", sender_password: str = "Info2021!", smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        self.sender_email = "info@jisparking.com"
        self.sender_password = "Info2021!"
        self.smtp_server = "server.jisparking.com"
        self.smtp_port = 465

    def send_email(self, receiver_email: str, subject: str, message: str):
        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = receiver_email
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "html"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, receiver_email, msg.as_string())

            return "Correo enviado correctamente"
        
        except smtplib.SMTPException as e:
            # Captura errores específicos de SMTP
            return f"Error al enviar el correo: {str(e)}"
        except Exception as e:
            # Captura cualquier otro tipo de error
            return f"Error inesperado al enviar el correo: {str(e)}"
