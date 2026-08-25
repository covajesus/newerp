import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailClass:
    def __init__(
        self,
        sender_email: str,
        sender_password: str,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 465,
        db=None,
    ):
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.db = db

    def _log_error(self, message: str, *, detail=None, exc=None, receiver_email: str | None = None):
        if not self.db:
            return
        try:
            from app.backend.classes.log_class import LogClass

            LogClass(self.db).log_error(
                "email_send",
                message,
                process_name="Email - Envío",
                reference_type="email",
                detail=detail or (f"to={receiver_email}" if receiver_email else None),
                exc=exc,
                error_code="smtp",
            )
        except Exception as log_exc:
            print(f"EmailClass log failed: {log_exc}")

    def send_email(self, receiver_email: str, subject: str, message: str):
        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = receiver_email
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "html"))

            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, receiver_email, msg.as_string())

            return "Correo enviado correctamente"

        except smtplib.SMTPAuthenticationError as e:
            err = "Error de autenticación: Verifica tu email y contraseña (usa una contraseña de aplicación si es Gmail)"
            self._log_error(err, detail=f"to={receiver_email}; subject={subject}", exc=e, receiver_email=receiver_email)
            return err
        except smtplib.SMTPException as e:
            err = f"Error al enviar el correo: {str(e)}"
            self._log_error(err, detail=f"to={receiver_email}; subject={subject}", exc=e, receiver_email=receiver_email)
            return err
        except Exception as e:
            err = f"Error inesperado al enviar el correo: {str(e)}"
            self._log_error(err, detail=f"to={receiver_email}; subject={subject}", exc=e, receiver_email=receiver_email)
            return err
