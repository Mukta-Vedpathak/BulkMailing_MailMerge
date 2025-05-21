import base64
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List

from app.email_utils import send_email
from app.email_schema import EmailRequest, EmailAttachment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Advanced Email Sending API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting configuration
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["50/minute"]  # Increased from 5/minute to 50/minute
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/send-email/")
@limiter.limit("50/minute")  # Increased from 5/minute to 50/minute
async def send_email_endpoint(
    request: Request,
    email_data: EmailRequest,
    background_tasks: BackgroundTasks
):
    """
    Endpoint to send emails.
    """
    try:
        if not email_data.recipients:
            raise HTTPException(status_code=400, detail="At least one recipient is required")

        if email_data.attachments:
            for attachment in email_data.attachments:
                try:
                    base64.b64decode(attachment.content)  # Validate base64 encoding
                except Exception:
                    raise HTTPException(status_code=400, detail=f"Invalid base64 content in attachment: {attachment.filename}")

        background_tasks.add_task(
            send_email,
            subject=email_data.subject,
            body=email_data.body,
            recipients=email_data.recipients,
            attachments=email_data.attachments,
            embedded_links=email_data.embedded_links,
            cc=email_data.cc,
            bcc=email_data.bcc
        )

        return {
            "message": f"Email is being sent to {len(email_data.recipients)} recipients",
            "recipients_count": len(email_data.recipients)
        }

    except Exception as e:
        logger.error(f"Error while sending email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-attachments/")
async def upload_attachments(files: List[UploadFile] = File(...)):
    """
    Endpoint to upload attachments.
    """
    attachments = []
    for file in files:
        content = await file.read()
        encoded_content = base64.b64encode(content).decode('utf-8')

        attachment = EmailAttachment(
            filename=file.filename,
            content=encoded_content,
            mime_type=file.content_type or 'application/octet-stream'
        )
        attachments.append(attachment)

    return {
        "message": f"Successfully uploaded {len(attachments)} files",
        "attachments": [{"filename": a.filename, "mime_type": a.mime_type} for a in attachments]
    }
