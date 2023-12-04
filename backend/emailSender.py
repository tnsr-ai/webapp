import smtplib
import ssl 
import os 
from dotenv import load_dotenv
load_dotenv()

class EmailSender:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = os.getenv("SMTP_PORT")
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        context = ssl.create_default_context()
        self.smtp_session = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
    
    def get_session(self):
        self.smtp_session.login(self.smtp_username, self.smtp_password)
        return self.smtp_session