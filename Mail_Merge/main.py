from bulk_emailer import BulkEmailer
import os

def main():
    # Email configuration
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    
    # Your email settings
    EMAIL = "jashwanthyerra2404@gmail.com"
    PASSWORD = "akoz kuar brym oyzm"
    
    # Initialize the bulk emailer
    emailer = BulkEmailer(SMTP_SERVER, SMTP_PORT, EMAIL, PASSWORD)
    
    # Example recipient list (keep the batch size reasonable)
    recipients = [
        "jashusunny2004@gmail.com",
        "jashuyerrab2@gmail.com"
    ]
    
    # Professional email content with proper formatting
    subject = "Important Update from Jashwanth"  # Use a clear, specific subject
    
    # Create a well-structured email body
    body = """
    Dear Recipient,
    
    I hope this email finds you well. 
    
    This is an important message regarding our upcoming plans.
    
    Key Points:
    • First important point
    • Second important point
    • Third important point
    
    Please find the attached documents for your reference.
    
    If you have any questions, please don't hesitate to reach out.
    
    Best regards,
    Jashwanth Yerra
    
    ---
    If you wish to unsubscribe, please reply with 'unsubscribe' in the subject line.
    """
    
    # Example attachments - replace these paths with your actual file paths
    attachments = [
        '/Users/jashwanthyerra/Desktop/Screenshot 2025-03-27 at 8.05.51 PM.png'  # Replace with actual PDF path       # Replace with actual image path
        # Add more attachments as needed
    ]
    
    # Send the bulk emails with attachments and improved delay settings
    emailer.send_bulk_emails(
        subject=subject,
        body=body,
        recipient_list=recipients,
        attachments=attachments,  # Added attachments parameter
        delay=3  # Increased delay between emails to reduce spam likelihood
    )

if __name__ == "__main__":
    main()