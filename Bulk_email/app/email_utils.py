import os
import asyncio
import logging
import base64
from typing import List, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from aiosmtplib import send
from app.email_schema import EmailAttachment
from dotenv import load_dotenv


# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def create_multipart_message(
    subject: str,
    body: str,
    sender: str,
    recipients: List[str],
    attachments: Optional[List[EmailAttachment]] = None,
    embedded_links: Optional[List[str]] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
) -> MIMEMultipart:
    """
    Create a multipart email message with advanced features.
    """
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = ', '.join(recipients)

    # Add CC and BCC if provided
    if cc:
        message['Cc'] = ', '.join(cc)
    if bcc:
        message['Bcc'] = ', '.join(bcc)

    message['Subject'] = subject

    # Add body
    body_with_links = body
    if embedded_links:
        body_with_links += "\n\nAdditional Links:\n" + "\n".join(embedded_links)

    message.attach(MIMEText(body_with_links, 'html'))

    # Add attachments
    if attachments:
        for attachment in attachments:
            decoded_content = base64.b64decode(attachment.content)

            if attachment.mime_type.startswith('image/'):
                mime_subtype = attachment.mime_type.split('/')[1]  # Extract MIME subtype
                part = MIMEImage(decoded_content, _subtype=mime_subtype, name=attachment.filename)
            elif attachment.mime_type.startswith('application/'):
                part = MIMEApplication(decoded_content, name=attachment.filename)
            else:
                part = MIMEApplication(decoded_content, name=attachment.filename)

            part['Content-Disposition'] = f'attachment; filename="{attachment.filename}"'
            message.attach(part)

    return message

async def send_individual_email(
    recipient: str,
    message: MIMEMultipart,
    smtp_server: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
) -> bool:
    """Send individual email with robust error handling."""
    try:
        await send(
            message,
            hostname=smtp_server,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            start_tls=True,
        )
        logger.info(f"Email sent successfully to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {e}")
        return False

async def send_email(
    subject: str,
    body: str,
    recipients: List[str],
    attachments: Optional[List[EmailAttachment]] = None,
    embedded_links: Optional[List[str]] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
):
    """
    Send emails concurrently in batches of 10 recipients per thread with rate limiting and retries.
    """
    # Load SMTP credentials dynamically
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    # Process recipients in batches of 10
    batch_size = 10
    all_recipients = recipients.copy()
    if cc:
        all_recipients.extend(cc)
    if bcc:
        all_recipients.extend(bcc)

    # Split recipients into batches
    recipient_batches = [all_recipients[i:i + batch_size] for i in range(0, len(all_recipients), batch_size)]

    # Rate limiting parameters
    max_retries = 3
    delay_between_batches = 2  # seconds
    max_concurrent_batches = 5  # Limit concurrent batches to avoid overwhelming the SMTP server

    # Limit concurrent tasks
    semaphore = asyncio.Semaphore(max_concurrent_batches)

    async def send_batch(batch_recipients, batch_number):
        async with semaphore:
            for retry in range(max_retries):
                try:
                    # Create a new message for this batch
                    batch_message = MIMEMultipart()
                    batch_message['From'] = smtp_user
                    batch_message['To'] = ', '.join(batch_recipients)
                    batch_message['Subject'] = subject

                    # Add body
                    body_with_links = body
                    if embedded_links:
                        body_with_links += "\n\nAdditional Links:\n" + "\n".join(embedded_links)

                    batch_message.attach(MIMEText(body_with_links, 'html'))

                    # Add attachments
                    if attachments:
                        for attachment in attachments:
                            decoded_content = base64.b64decode(attachment.content)

                            if attachment.mime_type.startswith('image/'):
                                mime_subtype = attachment.mime_type.split('/')[1]
                                part = MIMEImage(decoded_content, _subtype=mime_subtype, name=attachment.filename)
                            elif attachment.mime_type.startswith('application/'):
                                part = MIMEApplication(decoded_content, name=attachment.filename)
                            else:
                                part = MIMEApplication(decoded_content, name=attachment.filename)

                            part['Content-Disposition'] = f'attachment; filename="{attachment.filename}"'
                            batch_message.attach(part)
                    
                    await send(
                        batch_message,
                        hostname=smtp_server,
                        port=smtp_port,
                        username=smtp_user,
                        password=smtp_password,
                        start_tls=True,
                    )
                    logger.info(f"Batch {batch_number}: Email sent successfully to {len(batch_recipients)} recipients")
                    return True
                except Exception as e:
                    if retry < max_retries - 1:
                        wait_time = (retry + 1) * 5  # Exponential backoff
                        logger.warning(f"Batch {batch_number}: Retry {retry + 1}/{max_retries} after {wait_time} seconds. Error: {e}")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Batch {batch_number}: Failed after {max_retries} retries. Error: {e}")
                        return False

    # Process batches with delays
    results = []
    for i, batch in enumerate(recipient_batches):
        if i > 0:  # Add delay between batches, but not before the first batch
            await asyncio.sleep(delay_between_batches)
        result = await send_batch(batch, i + 1)
        results.append(result)

    # Log results
    successful = sum(1 for result in results if result is True)
    failed = len(recipient_batches) - successful
    logger.info(f"Email send summary: Successful batches: {successful}, Failed batches: {failed}")
