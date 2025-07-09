import os
import ssl
import smtplib
from dotenv import load_dotenv
from email.message import EmailMessage

class EmailSender:
    def __init__(self, sender_email=None, smtp_server="smtp.gmail.com", smtp_port=465):
        load_dotenv()
        self.sender_email = sender_email or os.getenv("GMAIL_EMAIL")
        self.email_pass = os.getenv("GMAIL_APP_PASSWORD")
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port

    def build_html(self, body_text, table_html=None):
        if table_html:
            html_content = f"""
            <html>
                <head>
                    <style>
                        .dataframe {{
                            width: 100%;
                            border-collapse: collapse;
                            font-family: Arial, sans-serif;
                        }}
                        .dataframe th, .dataframe td {{
                            border: 1px solid #ddd;
                            padding: 8px;
                            text-align: center;
                        }}
                        .dataframe th {{
                            background-color: #f2f2f2;
                            color: black;
                        }}
                        .dataframe tr:nth-child(even) {{
                            background-color: #f9f9f9;
                        }}
                        .dataframe tr:hover {{
                            background-color: #ddd;
                        }}
                    </style>
                </head>
                <body>
                    <p>{body_text}</p>
                    <br>
                    {table_html}
                </body>
            </html>
            """
        else:
            html_content = f"<html><body><p>{body_text}</p></body></html>"

        return html_content

    def send_email(self, recipient_email, subject, body_text, table_html, attachments=[]):
        """
        Send an email with optional DataFrame and attachments.
        """
        msg = EmailMessage()
        msg['From'] = self.sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject

        html_content = self.build_html(body_text, table_html)
        msg.set_content(html_content, subtype='html')

        for file_path in attachments:
            with open(file_path, 'rb') as f:
                file_data = f.read()
                file_name = os.path.basename(file_path)
                # Adjust maintype/subtype based on your attachments if needed
                msg.add_attachment(file_data,
                                   maintype="application",
                                   subtype="octet-stream",
                                   filename=file_name)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as server:
            server.login(self.sender_email, self.email_pass)
            server.send_message(msg)

        print(f"Email sent to {recipient_email}")
