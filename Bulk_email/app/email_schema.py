from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from fastapi import File, UploadFile

class EmailAttachment(BaseModel):
    filename: str
    content: bytes
    mime_type: str

class EmailRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    recipients: List[EmailStr]
    attachments: Optional[List[EmailAttachment]] = None
    embedded_links: Optional[List[str]] = None
    cc: Optional[List[EmailStr]] = None
    bcc: Optional[List[EmailStr]] = None