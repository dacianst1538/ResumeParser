import re
from typing import Optional, Tuple

# Lines to skip when looking for name at top of resume
_SKIP_PATTERNS = re.compile(
    r"^(?:curriculum\s*vitae|resume|cv|page\s*\d|confidential)",
    re.IGNORECASE
)

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"[\+]?\d[\d\s\-\(\)\.]{6,}")
_URL_RE = re.compile(r"https?://|www\.|linkedin|github", re.IGNORECASE)
_DATE_RE = re.compile(r"\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}")

# Common non-name words that appear in resume headers
_NON_NAME_WORDS = {
    "address", "email", "phone", "mobile", "tel", "fax", "objective",
    "summary", "experience", "education", "skills", "profile", "contact",
    "information", "details", "personal", "career", "professional",
    "resume", "curriculum", "vitae", "cv", "date", "birth", "gender",
    "nationality", "marital", "status", "languages", "references",
}

# Common Indian/Western name prefixes
_NAME_PREFIXES = re.compile(
    r"^(?:Mr\.?|Mrs\.?|Ms\.?|Dr\.?|Prof\.?|Shri\.?|Smt\.?)\s+",
    re.IGNORECASE
)


def _is_contact_line(line: str) -> bool:
    stripped = line.strip()
    if _EMAIL_RE.search(stripped):
        return True
    if _URL_RE.search(stripped):
        return True
    if _DATE_RE.search(stripped):
        return True
    # Line is mostly digits/symbols (phone number line)
    alpha_count = sum(1 for c in stripped if c.isalpha())
    digit_count = sum(1 for c in stripped if c.isdigit())
    if digit_count > alpha_count and len(stripped) > 5:
        return True
    return False


def _is_likely_name(text: str) -> bool:
    words = text.split()
    if not (1 <= len(words) <= 5):
        return False

    for w in words:
        clean = w.strip(".,()-")
        if not clean:
            continue
        # Each word should be mostly alphabetic
        if not re.match(r"^[A-Za-z\.\-']+$", clean):
            return False
        # Should not be a common non-name word
        if clean.lower() in _NON_NAME_WORDS:
            return False

    # At least one word should start with uppercase
    has_upper = any(w[0].isupper() for w in words if w)
    return has_upper


def _clean_name(name: str) -> Optional[str]:
    if not name:
        return None
    # Remove prefixes
    name = _NAME_PREFIXES.sub("", name).strip()
    # Remove suffixes
    name = re.sub(r"\s+(?:Jr\.?|Sr\.?|II|III|IV)$", "", name, flags=re.IGNORECASE)
    name = name.strip()
    if _is_likely_name(name):
        return name
    return None


def extract_name(text: str, **kwargs) -> Tuple[Optional[str], float]:
    lines = text.split("\n")

    # Strategy 1: First non-empty, non-contact, non-skip line in first 10 lines
    for line in lines[:10]:
        stripped = line.strip()
        if not stripped:
            continue
        if _SKIP_PATTERNS.match(stripped):
            continue
        if _is_contact_line(stripped):
            continue
        if len(stripped) > 50:
            continue

        # Check if this line has a pipe/dash separator (e.g., "John Doe | Software Engineer")
        parts = re.split(r"\s*[\|–—]\s*", stripped)
        for part in parts:
            cleaned = _clean_name(part.strip())
            if cleaned:
                # Higher confidence if it's the very first meaningful line
                return cleaned, 0.88

    # Strategy 2: Look for "Name:" label
    for line in lines[:15]:
        label_match = re.match(
            r"(?:name|full\s*name|candidate\s*name)\s*[:\-–—]\s*(.+)",
            line.strip(), re.IGNORECASE
        )
        if label_match:
            cleaned = _clean_name(label_match.group(1).strip())
            if cleaned:
                return cleaned, 0.92

    # Strategy 3: First line that looks like a name (2-4 capitalized words)
    for line in lines[:8]:
        stripped = line.strip()
        if not stripped or len(stripped) > 40:
            continue
        words = stripped.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w and w[0].isalpha()):
            cleaned = _clean_name(stripped)
            if cleaned:
                return cleaned, 0.70

    return None, 0.0
