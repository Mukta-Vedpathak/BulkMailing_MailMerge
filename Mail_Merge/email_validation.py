from email_validator import validate_email as validate_email_address, EmailNotValidError
from typing import List, Dict, Tuple
import dns.resolver
import re

class EmailAddressValidator:
    @staticmethod
    def _check_domain_mx(domain: str) -> bool:
        """Check if the domain has valid MX records"""
        try:
            dns.resolver.resolve(domain, 'MX')
            return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            return False

    @staticmethod
    def validate_single_email(email: str) -> Tuple[bool, str]:
        """Validate a single email address with enhanced checks"""
        try:
            # Basic pattern check before detailed validation
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, email):
                return False, "Invalid email format"

            # Check for invalid domain patterns
            local_part, domain = email.split('@')
            
            # Check for consecutive dots
            if '..' in domain:
                return False, "Domain cannot contain consecutive dots"
                
            # Check for invalid TLD (too long or has consecutive dots)
            tld = domain.split('.')[-1]
            if len(tld) > 6 or '..' in tld:
                return False, "Invalid top-level domain"

            # Basic email validation
            try:
                validated = validate_email_address(email, check_deliverability=True)
                email = validated.normalized
                return True, ""
            except EmailNotValidError as e:
                return False, str(e)

        except Exception as e:
            return False, f"Invalid email format: {str(e)}"

    @staticmethod
    def validate_email_lists(to_list: List[str], cc_list: List[str] = None, bcc_list: List[str] = None) -> Tuple[bool, Dict[str, List[str]], Dict[str, List[str]]]:
        if cc_list is None:
            cc_list = []
        if bcc_list is None:
            bcc_list = []

        invalid_emails = {
            'to': [],
            'cc': [],
            'bcc': []
        }
        valid_emails = {
            'to': [],
            'cc': [],
            'bcc': []
        }

        # Validate TO list
        for email in to_list:
            is_valid, _ = EmailAddressValidator.validate_single_email(email)
            if is_valid:
                valid_emails['to'].append(email)
            else:
                invalid_emails['to'].append(email)

        # Validate CC list
        for email in cc_list:
            is_valid, _ = EmailAddressValidator.validate_single_email(email)
            if is_valid:
                valid_emails['cc'].append(email)
            else:
                invalid_emails['cc'].append(email)

        # Validate BCC list
        for email in bcc_list:
            is_valid, _ = EmailAddressValidator.validate_single_email(email)
            if is_valid:
                valid_emails['bcc'].append(email)
            else:
                invalid_emails['bcc'].append(email)

        # Return validation status, invalid emails dict, and valid emails dict
        has_invalid = any(len(emails) > 0 for emails in invalid_emails.values())
        return (not has_invalid), invalid_emails, valid_emails