import re
from typing import Optional, List, Dict

_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)

_PHONE_RE = re.compile(
    r"(?:\+?\d{1,3}[\s\-.]?)?"
    r"(?:\(?\d{2,5}\)?[\s\-.]?)?"
    r"\d{3,5}[\s\-.]?\d{3,5}"
    r"(?:\s*(?:ext|x|extension)\.?\s*\d{1,5})?",
    re.IGNORECASE
)

_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:linkedin\.com/in/[\w\-]+|github\.com/[\w\-]+|[\w\-]+\.(?:com|org|net|io|dev|me)/[\w\-/]*)",
    re.IGNORECASE
)

_DOB_LABELS = re.compile(
    r"(?:date\s*of\s*birth|d\.?o\.?b\.?|birth\s*date|born)\s*[:\-–—]?\s*",
    re.IGNORECASE
)

_DATE_PATTERNS = [
    r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}",
    r"\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2}",
    r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{2,4}",
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{2,4}",
]


def _get_header_text(text: str, max_lines: int = 15) -> str:
    """Extract only the header portion of the resume for contact info."""
    lines = text.split("\n")
    return "\n".join(lines[:max_lines])


def extract_emails(text: str) -> List[str]:
    found = _EMAIL_RE.findall(text)
    seen = set()
    result = []
    for e in found:
        lower = e.lower()
        if lower not in seen:
            seen.add(lower)
            result.append(lower)
    return result


def extract_phones(text: str) -> List[str]:
    candidates = _PHONE_RE.findall(text)
    phones = []
    seen = set()
    for raw in candidates:
        digits = re.sub(r"[^\d]", "", raw)
        if 7 <= len(digits) <= 15 and digits not in seen:
            seen.add(digits)
            phones.append(raw.strip())
    return phones


def extract_urls(text: str) -> List[str]:
    return list(set(_URL_RE.findall(text)))


def extract_dob(text: str) -> Optional[str]:
    for line in text.split("\n"):
        label_match = _DOB_LABELS.search(line)
        if label_match:
            after = line[label_match.end():]
            for pat in _DATE_PATTERNS:
                m = re.search(pat, after, re.IGNORECASE)
                if m:
                    return m.group(0).strip()
    return None


def extract_contacts(text: str) -> Dict:
    """Extract contacts from header section only to avoid multi-resume pollution."""
    header = _get_header_text(text)

    emails = extract_emails(header)
    phones = extract_phones(header)
    urls = extract_urls(header)
    dob = extract_dob(header)

    return {
        "emails": emails,
        "phoneNumbers": phones,
        "websites": urls,
        "dateOfBirth": dob,
        "confidence": {
            "emails": 0.99 if emails else 0.0,
            "phoneNumbers": 0.95 if phones else 0.0,
            "websites": 0.97 if urls else 0.0,
            "dateOfBirth": 0.85 if dob else 0.0,
        }
    }
