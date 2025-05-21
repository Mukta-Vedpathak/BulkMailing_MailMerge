import smtplib
import os
import mimetypes
from email.message import EmailMessage
from typing import List, Optional, Tuple, Dict
import time
from text_cleaner import TextCleaner
from email_validation import EmailAddressValidator
import copy

class BulkEmailer:
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.cleaner = TextCleaner()
        self.email_validator = EmailAddressValidator()

    def _add_attachment(self, message: EmailMessage, filepath: str) -> None:
        """Add an attachment to the email message"""
        try:
            # Guess the content type of the file
            content_type, encoding = mimetypes.guess_type(filepath)
            if content_type is None or encoding is not None:
                content_type = 'application/octet-stream'
            maintype, subtype = content_type.split('/', 1)
            
            with open(filepath, 'rb') as f:
                message.add_attachment(
                    f.read(),
                    maintype=maintype,
                    subtype=subtype,
                    filename=os.path.basename(filepath)
                )
        except Exception as e:
            print(f"Failed to attach file {filepath}: {str(e)}")

    def validate_emails(self) -> Tuple[bool, Dict[str, List[str]], List[str]]:
        """Validate all email addresses in the message"""
        return EmailAddressValidator.validate_email_lists(
            self.to_list,
            self.cc_list,
            self.bcc_list
        )

    def send_bulk_emails(self, subject: str, body: str, recipient_list: List[str], 
                        cc_list: Optional[List[str]] = None, 
                        bcc_list: Optional[List[str]] = None,
                        attachments: Optional[List[str]] = None, 
                        delay: int = 2):
        try:
            # Clean all text inputs before processing
            subject = self.cleaner.clean_text(subject)
            body = self.cleaner.clean_text(body)
            
            # Initial validation of all email addresses
            for email in recipient_list:
                is_valid, error_msg = EmailAddressValidator.validate_single_email(email)
                if not is_valid:
                    raise ValueError(f"Invalid recipient email: {email} - {error_msg}")

            if cc_list:
                for email in cc_list:
                    is_valid, error_msg = EmailAddressValidator.validate_single_email(email)
                    if not is_valid:
                        raise ValueError(f"Invalid CC email: {email} - {error_msg}")

            if bcc_list:
                for email in bcc_list:
                    is_valid, error_msg = EmailAddressValidator.validate_single_email(email)
                    if not is_valid:
                        raise ValueError(f"Invalid BCC email: {email} - {error_msg}")

            # Connect to SMTP server first to test connection
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                
                # For each primary recipient
                for recipient in recipient_list:
                    try:
                        # Create a new message for each recipient
                        message = EmailMessage()
                        message['From'] = f"Jashwanth Yerra <{self.username}>"
                        message['Subject'] = subject
                        message['To'] = recipient
                        
                        # Add essential headers to reduce spam likelihood
                        message['Message-ID'] = EmailMessage().get('Message-ID')
                        message['Date'] = EmailMessage().get('Date')
                        message['MIME-Version'] = '1.0'
                        
                        # Set CC if provided
                        if cc_list and len(cc_list) > 0:
                            message['Cc'] = ', '.join(cc_list)
                        
                        # Set the body with UTF-8 encoding
                        message.set_content(body, charset='utf-8')
                        
                        # Add HTML version of the body with improved formatting
                        html_body = f"""
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        </head>
                        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                            {body.replace('\\n', '<br>')}
                        </body>
                        </html>
                        """
                        message.add_alternative(html_body, subtype='html', charset='utf-8')
                        
                        # Add attachments if any
                        if attachments:
                            for attachment_path in attachments:
                                if os.path.exists(attachment_path):
                                    self._add_attachment(message, attachment_path)
                        
                        # Set all recipients for sending
                        all_recipients = [recipient]
                        if cc_list:
                            all_recipients.extend(cc_list)
                        if bcc_list:
                            all_recipients.extend(bcc_list)
                        
                        # Add List-Unsubscribe header
                        message['List-Unsubscribe'] = f'<mailto:{self.username}?subject=unsubscribe>'
                        
                        # Send the message
                        server.send_message(message, to_addrs=all_recipients)
                        print(f"Successfully sent email to {recipient} with CC/BCC")
                        
                        # Dynamic delay based on batch size
                        batch_size = len(recipient_list)
                        if batch_size > 10:
                            time.sleep(delay * 2)  # Increased delay for larger batches
                        else:
                            time.sleep(delay)
                        
                    except Exception as e:
                        print(f"Failed to send email to {recipient}: {str(e)}")
                        raise  # Re-raise the exception to be caught by the outer try block
                        
        except Exception as e:
            error_msg = str(e)
            print(f"Email sending failed: {error_msg}")
            raise Exception(f"Email sending failed: {error_msg}")