# Bulk Email Sender with Templates

A Flask-based web application for sending personalized bulk emails with template support. This application allows you to create reusable email templates, send emails to multiple recipients with personalization, and manage attachments efficiently.

## Features

- 📧 Send bulk emails to multiple recipients
- 📝 Create and manage reusable email templates
- 🔄 Variable support for email personalization
- 📎 Support for file attachments
- 👥 CC and BCC recipient support
- 🔒 Secure Gmail authentication with App Passwords
- 🎨 Clean and responsive Bootstrap UI

## Prerequisites

- Python 3.x
- Flask and its dependencies
- Gmail account with App Password enabled

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd emailapp
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

### Creating Email Templates

1. In the "Email Templates" section:
   - Enter a template name
   - Define the subject template with variables: e.g., "Welcome to {company}, {name}!"
   - Write the body template using variables: e.g., "Dear {name}, ..."
   - Click "Save Template"

### Sending Emails

1. Fill in your Gmail credentials:
   - Enter your Gmail address
   - Use an App Password (not your regular Gmail password)

2. Select a template or write a custom email

3. Enter recipients with their personalization variables:
```
john@example.com,name=John,company=Acme Inc
jane@example.com,name=Jane,company=TechCorp
```

4. Optionally add:
   - CC recipients
   - BCC recipients
   - File attachments

5. Click "Send Emails"

## Security Notes

- Never commit your email credentials
- Always use Gmail App Passwords instead of your main password
- The application uses environment variables for sensitive data

## Template Variables

Variables in templates are denoted by curly braces: {variable_name}

Example template:
```
Subject: Welcome to {company}, {name}!

Dear {name},

Welcome to {company}! We're excited to have you join us.

Best regards,
{sender_name}
```

## File Structure

- `app.py`: Main Flask application
- `bulk_emailer.py`: Email sending functionality
- `email_template.py`: Template management
- `text_cleaner.py`: Text sanitization
- `templates/`: HTML templates and email templates
- `uploads/`: Temporary storage for attachments

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
