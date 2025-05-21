import json
import os
from typing import Dict, List, Optional

class EmailTemplate:
    def __init__(self, name: str, subject: str, body: str, variables: Optional[List[str]] = None):
        self.name = name
        self.subject = subject
        self.body = body
        self.variables = variables or self._extract_variables()

    def _extract_variables(self) -> List[str]:
        """Extract variables from the template (anything in {curly braces})"""
        import re
        variables = set()
        # Find all {variable_name} in both subject and body
        pattern = r'\{([^}]+)\}'
        variables.update(re.findall(pattern, self.subject))
        variables.update(re.findall(pattern, self.body))
        return sorted(list(variables))

    def render(self, recipient_data: Dict[str, str]) -> tuple[str, str]:
        """Render the template with the given variables"""
        subject = self.subject
        body = self.body
        
        # Replace each variable in both subject and body
        for var_name, value in recipient_data.items():
            placeholder = '{' + var_name + '}'
            subject = subject.replace(placeholder, value)
            body = body.replace(placeholder, value)
            
        return subject, body

class TemplateManager:
    def __init__(self, templates_dir: str = 'templates'):
        self.templates_dir = templates_dir
        self.templates_file = os.path.join(templates_dir, 'email_templates.json')
        self._ensure_templates_dir()
        self.templates: Dict[str, EmailTemplate] = self._load_templates()

    def _ensure_templates_dir(self):
        """Ensure the templates directory exists"""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
        if not os.path.exists(self.templates_file):
            self._save_templates({})

    def _load_templates(self) -> Dict[str, EmailTemplate]:
        """Load templates from JSON file"""
        try:
            with open(self.templates_file, 'r') as f:
                data = json.load(f)
                return {
                    name: EmailTemplate(
                        name=template['name'],
                        subject=template['subject'],
                        body=template['body'],
                        variables=template.get('variables')
                    )
                    for name, template in data.items()
                }
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_templates(self, templates_dict: dict):
        """Save templates to JSON file"""
        with open(self.templates_file, 'w') as f:
            json.dump(templates_dict, f, indent=4)

    def save_template(self, template: EmailTemplate):
        """Save or update a template"""
        templates_dict = {
            name: {
                'name': t.name,
                'subject': t.subject,
                'body': t.body,
                'variables': t.variables
            }
            for name, t in self.templates.items()
        }
        templates_dict[template.name] = {
            'name': template.name,
            'subject': template.subject,
            'body': template.body,
            'variables': template.variables
        }
        self._save_templates(templates_dict)
        self.templates[template.name] = template

    def get_template(self, name: str) -> Optional[EmailTemplate]:
        """Get a template by name"""
        return self.templates.get(name)

    def list_templates(self) -> List[str]:
        """List all template names"""
        return list(self.templates.keys())

    def delete_template(self, name: str) -> bool:
        """Delete a template by name"""
        if name in self.templates:
            templates_dict = {
                n: {
                    'name': t.name,
                    'subject': t.subject,
                    'body': t.body,
                    'variables': t.variables
                }
                for n, t in self.templates.items()
                if n != name
            }
            self._save_templates(templates_dict)
            del self.templates[name]
            return True
        return False