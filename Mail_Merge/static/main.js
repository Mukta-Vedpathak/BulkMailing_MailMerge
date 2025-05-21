document.addEventListener('DOMContentLoaded', function() {
    const templateSelect = document.querySelector('#template');
    const subjectField = document.querySelector('#subject');
    const bodyField = document.querySelector('#body');
    const templateVarsHint = document.querySelector('.template-variables');
    const emailForm = document.querySelector('#email-form');
    const loadingOverlay = document.querySelector('.loading-overlay');
    const attachmentsInput = document.querySelector('#attachments-input');
    const attachmentPreview = document.querySelector('#attachment-preview');
    const deleteButtons = document.querySelectorAll('.delete-template');
    const editButtons = document.querySelectorAll('.edit-template');
    const templateForm = document.querySelector('#template-form');
    const templateFormTitle = document.querySelector('#template-form-title');
    const cancelEditButton = document.querySelector('#cancel-edit');
    const isEditInput = document.querySelector('#is_edit');
    const templateNameField = document.querySelector('#name');

    // Template editing handler
    editButtons.forEach(button => {
        button.addEventListener('click', function() {
            const templateName = this.dataset.templateName;
            fetch(`/templates/${templateName}`)
                .then(response => response.json())
                .then(template => {
                    // Switch form to edit mode
                    templateFormTitle.innerHTML = `<i class="fas fa-edit me-2"></i>Edit Template: ${templateName}`;
                    templateNameField.value = template.name;
                    templateNameField.readOnly = true;
                    templateForm.querySelector('#subject').value = template.subject;
                    templateForm.querySelector('#body').value = template.body;
                    isEditInput.value = 'true';
                    cancelEditButton.style.display = 'inline-block';
                    
                    // Scroll to the form
                    templateForm.scrollIntoView({ behavior: 'smooth' });
                })
                .catch(error => console.error('Error:', error));
        });
    });

    // Cancel edit handler
    cancelEditButton.addEventListener('click', function() {
        // Reset form to create mode
        templateFormTitle.innerHTML = '<i class="fas fa-plus-circle me-2"></i>Create New Template';
        templateForm.reset();
        templateNameField.readOnly = false;
        isEditInput.value = 'false';
        this.style.display = 'none';
    });

    // Template deletion handler
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const templateName = this.dataset.templateName;
            if (confirm(`Are you sure you want to delete the template "${templateName}"?`)) {
                fetch(`/templates/${templateName}`, {
                    method: 'DELETE'
                })
                .then(response => response.json())
                .then(data => {
                    if (data.message) {
                        // Remove template from the list
                        this.closest('.template-item').remove();
                        
                        // Remove from template select dropdown
                        const option = templateSelect.querySelector(`option[value="${templateName}"]`);
                        if (option) {
                            option.remove();
                        }

                        // Show success message
                        const alert = document.createElement('div');
                        alert.className = 'alert alert-success alert-dismissible fade show';
                        alert.innerHTML = `
                            ${data.message}
                            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                        `;
                        document.querySelector('.flash-messages').appendChild(alert);

                        // Auto dismiss the message
                        setTimeout(() => {
                            alert.classList.remove('show');
                            setTimeout(() => alert.remove(), 300);
                        }, 5000);
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        });
    });

    // Template change handler
    templateSelect.addEventListener('change', function() {
        if (this.value) {
            fetch(`/templates/${this.value}`)
                .then(response => response.json())
                .then(template => {
                    subjectField.value = template.subject;
                    bodyField.value = template.body;
                    if (template.variables && template.variables.length > 0) {
                        templateVarsHint.querySelector('span').textContent = 
                            'Available variables: ' + template.variables.join(', ');
                        templateVarsHint.style.display = 'block';
                    } else {
                        templateVarsHint.style.display = 'none';
                    }
                })
                .catch(error => console.error('Error:', error));
        } else {
            subjectField.value = '';
            bodyField.value = '';
            templateVarsHint.style.display = 'none';
        }
    });

    // Form submission handler
    emailForm.addEventListener('submit', function() {
        loadingOverlay.style.display = 'flex';
    });

    // Attachment preview
    attachmentsInput.addEventListener('change', function() {
        attachmentPreview.innerHTML = '';
        Array.from(this.files).forEach(file => {
            const item = document.createElement('div');
            item.className = 'attachment-item';
            item.innerHTML = `
                <i class="fas fa-file"></i>
                <span>${file.name}</span>
            `;
            attachmentPreview.appendChild(item);
        });
    });

    // Auto-dismiss flash messages
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            message.classList.remove('show');
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
});