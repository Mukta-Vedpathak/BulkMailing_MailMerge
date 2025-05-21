from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, MultipleFileField, SelectField
from wtforms.validators import DataRequired, Email
import os
from bulk_emailer import BulkEmailer
from text_cleaner import TextCleaner
from email_template import TemplateManager, EmailTemplate
from email_validation import EmailAddressValidator
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import csv
from io import StringIO

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'
load_dotenv()

# Ensure upload folders exist
for folder in [app.config['UPLOAD_FOLDER'], 'templates']:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Initialize template manager
template_manager = TemplateManager()

class EmailForm(FlaskForm):
    sender_email = StringField('Sender Email', validators=[DataRequired(), Email()])
    sender_password = StringField('App Password', validators=[DataRequired()])
    template = SelectField('Email Template', choices=[('', 'No template - Write custom email')])
    recipients = TextAreaField('To (one email per line with optional variables)', validators=[DataRequired()])
    cc = TextAreaField('CC (one email per line)')
    bcc = TextAreaField('BCC (one email per line)')
    subject = StringField('Subject', validators=[DataRequired()])
    body = TextAreaField('Email Body', validators=[DataRequired()])
    attachments = MultipleFileField('Attachments')
    submit = SubmitField('Send Emails')

class TemplateForm(FlaskForm):
    name = StringField('Template Name', validators=[DataRequired()])
    subject = StringField('Subject Template', validators=[DataRequired()])
    body = TextAreaField('Body Template', validators=[DataRequired()])
    submit = SubmitField('Save Template')

def parse_recipient_line(line: str) -> tuple[str, dict]:
    """Parse a recipient line that may contain variables
    Format: email,var1=value1,var2=value2"""
    parts = [p.strip() for p in line.split(',')]
    email = parts[0]
    variables = {}
    
    for part in parts[1:]:
        if '=' in part:
            key, value = part.split('=', 1)
            variables[key.strip()] = value.strip()
            
    return email, variables

@app.route('/', methods=['GET', 'POST'])
def index():
    form = EmailForm()
    template_form = TemplateForm()
    cleaner = TextCleaner()
    
    # Update template choices
    templates = template_manager.list_templates()
    form.template.choices = [('', 'No template - Write custom email')] + [(t, t) for t in templates]
    
    if form.validate_on_submit():
        try:
            # Clean and validate sender email
            is_valid, error_message = EmailAddressValidator.validate_single_email(form.sender_email.data.strip())
            if not is_valid:
                flash(f'Invalid sender email: {error_message}', 'error')
                return render_template('index.html', form=form, template_form=template_form)

            # Clean all form inputs
            subject = cleaner.clean_text(form.subject.data)
            body = cleaner.clean_text(form.body.data)
            sender_email = form.sender_email.data.strip()
            sender_password = form.sender_password.data.strip()
            
            # Process recipients and their variables
            raw_recipients = []
            recipient_variables = []
            for line in form.recipients.data.split('\n'):
                if line.strip():
                    email, variables = parse_recipient_line(line.strip())
                    raw_recipients.append(email)
                    recipient_variables.append(variables)

            # Process CC and BCC lists
            cc_list = [email.strip() for email in form.cc.data.split('\n') if email.strip()] if form.cc.data else None
            bcc_list = [email.strip() for email in form.bcc.data.split('\n') if email.strip()] if form.bcc.data else None

            # Validate all email lists
            is_valid, invalid_emails, valid_emails = EmailAddressValidator.validate_email_lists(raw_recipients, cc_list, bcc_list)
            
            if not is_valid:
                if invalid_emails['to']:
                    flash(f'Invalid recipient emails: {", ".join(invalid_emails["to"])}', 'error')
                if invalid_emails['cc']:
                    flash(f'Invalid CC emails: {", ".join(invalid_emails["cc"])}', 'error')
                if invalid_emails['bcc']:
                    flash(f'Invalid BCC emails: {", ".join(invalid_emails["bcc"])}', 'error')
                return render_template('index.html', form=form, template_form=template_form)

            # Save attachments
            attachment_paths = []
            if form.attachments.data:
                for file in form.attachments.data:
                    if file.filename:
                        filename = cleaner.clean_text(secure_filename(file.filename))
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        attachment_paths.append(filepath)
            
            try:
                # Initialize bulk emailer
                emailer = BulkEmailer(
                    smtp_server="smtp.gmail.com",
                    smtp_port=587,
                    username=sender_email,
                    password=sender_password
                )
                
                # Get template if selected
                template = None
                if form.template.data:
                    template = template_manager.get_template(form.template.data)
                
                # Send emails with cleaned and validated data
                for i, recipient_email in enumerate(valid_emails['to']):
                    if template:
                        # Use template with personalization
                        personalized_subject, personalized_body = template.render(recipient_variables[i])
                    else:
                        # Use custom email with personalization
                        personalized_subject = subject
                        personalized_body = body
                        for var_name, value in recipient_variables[i].items():
                            placeholder = '{' + var_name + '}'
                            personalized_subject = personalized_subject.replace(placeholder, value)
                            personalized_body = personalized_body.replace(placeholder, value)
                    
                    emailer.send_bulk_emails(
                        subject=personalized_subject,
                        body=personalized_body,
                        recipient_list=[recipient_email],
                        cc_list=valid_emails.get('cc', []),
                        bcc_list=valid_emails.get('bcc', []),
                        attachments=attachment_paths
                    )
                
                flash('Emails sent successfully!', 'success')
                
            finally:
                # Clean up attachment files
                for path in attachment_paths:
                    if os.path.exists(path):
                        os.remove(path)
            
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Error sending emails: {str(e)}', 'error')
            # Clean up any remaining attachments in case of error
            try:
                for path in attachment_paths:
                    if os.path.exists(path):
                        os.remove(path)
            except:
                pass
    
    return render_template('index.html', form=form, template_form=template_form)

@app.route('/templates', methods=['POST'])
def save_template():
    template_form = TemplateForm()
    if template_form.validate_on_submit():
        try:
            template = EmailTemplate(
                name=template_form.name.data,
                subject=template_form.subject.data,
                body=template_form.body.data
            )
            is_edit = request.form.get('is_edit') == 'true'
            template_manager.save_template(template)
            
            if is_edit:
                flash(f'Template "{template.name}" updated successfully!', 'success')
            else:
                flash(f'Template "{template.name}" saved successfully!', 'success')
        except Exception as e:
            flash(f'Error saving template: {str(e)}', 'error')
    return redirect(url_for('index'))

@app.route('/templates/<template_name>', methods=['GET'])
def get_template(template_name):
    template = template_manager.get_template(template_name)
    if template:
        return jsonify({
            'name': template.name,
            'subject': template.subject,
            'body': template.body,
            'variables': template.variables
        })
    return jsonify({'error': 'Template not found'}), 404

@app.route('/templates/<template_name>', methods=['DELETE'])
def delete_template(template_name):
    if template_manager.delete_template(template_name):
        return jsonify({'message': f'Template "{template_name}" deleted successfully'})
    return jsonify({'error': 'Template not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)