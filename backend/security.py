import re

def redact_pii(text: str) -> str:
    """
    Redacts Personally Identifiable Information (PII) from lab reports.
    Protects patient privacy by filtering out names, DOBs, emails, phone numbers, and SSNs.
    """
    if not text:
        return ""
        
    redacted = text
    
    # 1. Redact Emails
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    redacted = re.sub(email_pattern, "[REDACTED EMAIL]", redacted)
    
    # 2. Redact Phone Numbers (various international formats)
    phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    redacted = re.sub(phone_pattern, "[REDACTED PHONE]", redacted)
    
    # 3. Redact Social Security Numbers or IDs (e.g. XXX-XX-XXXX or digits)
    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    redacted = re.sub(ssn_pattern, "[REDACTED ID]", redacted)
    
    # 4. Redact Patient Name patterns (e.g., "Patient Name: John Doe", "Patient: Jane Smith")
    name_patterns = [
        (r'(?i)patient\s+name\s*:\s*([A-Za-z\s]+)', "Patient Name: [REDACTED NAME]"),
        (r'(?i)patient\s*:\s*([A-Za-z\s]+)', "Patient: [REDACTED NAME]"),
        (r'(?i)client\s+name\s*:\s*([A-Za-z\s]+)', "Client Name: [REDACTED NAME]"),
    ]
    for pattern, replacement in name_patterns:
        # Match only lines that look like name labels
        def name_replacer(match):
            # Keep label, redact matched name
            prefix = match.group(0).split(':')[0] + ":"
            # If the value contains newline, stop at newline
            val = match.group(1).split('\n')[0].strip()
            # If it's short or has words like 'Age' or 'Male', be careful, but general redaction is fine
            return f"{prefix} [REDACTED NAME]"
            
        redacted = re.compile(pattern).sub(name_replacer, redacted)

    # 5. Redact Date of Birth patterns (e.g., "DOB: 10/10/1990", "Date of Birth: January 1, 1990")
    dob_patterns = [
        (r'(?i)dob\s*:\s*(\S+)', "DOB: [REDACTED DOB]"),
        (r'(?i)date\s+of\s+birth\s*:\s*([^\n]+)', "Date of Birth: [REDACTED DOB]"),
        (r'(?i)birth\s+date\s*:\s*([^\n]+)', "Birth Date: [REDACTED DOB]"),
    ]
    for pattern, replacement in dob_patterns:
        def dob_replacer(match):
            prefix = match.group(0).split(':')[0] + ":"
            return f"{prefix} [REDACTED DOB]"
        redacted = re.compile(pattern).sub(dob_replacer, redacted)

    # 6. Generic Address Redactor (e.g. "Address: 123 Main St...")
    address_patterns = [
        (r'(?i)address\s*:\s*([^\n]+)', "Address: [REDACTED ADDRESS]"),
    ]
    for pattern, replacement in address_patterns:
        def address_replacer(match):
            prefix = match.group(0).split(':')[0] + ":"
            return f"{prefix} [REDACTED ADDRESS]"
        redacted = re.compile(pattern).sub(address_replacer, redacted)

    return redacted
