import re
from typing import List, Dict

_DEGREE_RE = re.compile(
    r"\b(?:"
    r"Ph\.?D\.?|Doctorate|"
    r"M\.?(?:Tech|S|Sc|A|B\.?A|C\.?A|Com|E|Ed|Phil|Arch|Des|Pharm|P\.?H)"
    r"|Master(?:'?s)?(?:\s+of\s+\w+)?"
    r"|B\.?(?:Tech|S|Sc|A|B\.?A|C\.?A|Com|E|Ed|Arch|Des|Pharm|Eng)"
    r"|Bachelor(?:'?s)?(?:\s+of\s+\w+)?"
    r"|MBA|MCA|BCA|BBA|LLB|LLM"
    r"|Diploma|Post\s*Graduate\s*Diploma|PG\s*Diploma|PGDM"
    r"|(?:10th|12th|XII|X|HSC|SSC|CBSE|ICSE|ISC|Intermediate|Higher\s+Secondary|Senior\s+Secondary|Matriculation)"
    r")\b",
    re.IGNORECASE
)

# Fixed: non-capturing group so findall returns the full year
_YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")

_GPA_RE = re.compile(
    r"(?:(?:GPA|CGPA|CPI|SGPA)\s*[:\-]?\s*(\d+\.?\d*)\s*(?:/\s*\d+\.?\d*)?)"
    r"|(?:(\d{1,3}\.?\d*)\s*%)",
    re.IGNORECASE
)

_INSTITUTION_INDICATORS = re.compile(
    r"\b(?:university|institute|college|school|academy|polytechnic|IIT|NIT|IIIT|BITS|VIT|SRM|AIIMS)\b",
    re.IGNORECASE
)

# Words that should NOT appear in a field-of-study
_NON_FIELD_WORDS = re.compile(
    r"\b(?:university|institute|college|school|academy|polytechnic|IIT|NIT|IIIT|BITS|VIT|SRM|AIIMS|Indian|Delhi|Mumbai|Bangalore|Chennai|Hyderabad|Kolkata)\b",
    re.IGNORECASE
)


def extract_education(section_text: str) -> List[Dict]:
    if not section_text or not section_text.strip():
        return []

    entries = []
    lines = section_text.strip().split("\n")
    current_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_lines:
                entry = _parse_education_block("\n".join(current_lines))
                if entry.get("degree") or entry.get("institution"):
                    entries.append(entry)
                current_lines = []
            continue

        # New entry if line has a degree and we already have lines with a degree
        degree_match = _DEGREE_RE.search(stripped)
        if degree_match and current_lines:
            prev_text = "\n".join(current_lines)
            if _DEGREE_RE.search(prev_text):
                entry = _parse_education_block(prev_text)
                if entry.get("degree") or entry.get("institution"):
                    entries.append(entry)
                current_lines = [stripped]
                continue

        current_lines.append(stripped)

    if current_lines:
        entry = _parse_education_block("\n".join(current_lines))
        if entry.get("degree") or entry.get("institution"):
            entries.append(entry)

    if not entries:
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if _DEGREE_RE.search(stripped) or _INSTITUTION_INDICATORS.search(stripped):
                entry = _parse_education_block(stripped)
                if entry.get("degree") or entry.get("institution"):
                    entries.append(entry)

    return entries


def _parse_education_block(block: str) -> Dict:
    entry: Dict = {
        "degree": None,
        "institution": None,
        "year": None,
        "gpa": None,
        "field": None,
    }

    block_lines = block.split("\n")

    # Extract degree
    degree_match = _DEGREE_RE.search(block)
    if degree_match:
        entry["degree"] = degree_match.group(0).strip()

        # Field of study — only from the SAME LINE as the degree, after the degree
        degree_line = None
        for line in block_lines:
            if degree_match.group(0) in line:
                degree_line = line
                break

        if degree_line:
            after_degree = degree_line[degree_line.index(degree_match.group(0)) + len(degree_match.group(0)):].strip()
            field_match = re.match(
                r"[\s\-–—,]*(?:in\s+|[\(\-–—]\s*)?([A-Za-z\s&]+?)(?:\s*[\)\-–—,]|\s*\d|\s*$)",
                after_degree
            )
            if field_match:
                field = field_match.group(1).strip()
                # Strip any newline leakage
                field = field.split("\n")[0].strip()
                # Must be a real field name, not institution/city
                if 3 < len(field) < 50 and not _YEAR_RE.search(field) and not _NON_FIELD_WORDS.search(field):
                    entry["field"] = field

    # Extract institution — look for line with institution indicator
    for line in block_lines:
        if _INSTITUTION_INDICATORS.search(line):
            inst_text = line.strip()
            # Remove degree from this line if present
            if entry["degree"]:
                inst_text = re.sub(re.escape(entry["degree"]), "", inst_text, flags=re.IGNORECASE)
            # Remove field
            if entry["field"]:
                inst_text = re.sub(re.escape(entry["field"]), "", inst_text, flags=re.IGNORECASE)
            # Remove "in" connector
            inst_text = re.sub(r"\bin\b", "", inst_text, flags=re.IGNORECASE)
            # Remove years and GPA
            inst_text = _YEAR_RE.sub("", inst_text)
            inst_text = _GPA_RE.sub("", inst_text)
            inst_text = re.sub(r"[,\-–—\|\s]+$", "", inst_text).strip()
            inst_text = re.sub(r"^[,\-–—\|\s]+", "", inst_text).strip()
            if inst_text and len(inst_text) > 3:
                entry["institution"] = inst_text
                break

    # Extract years — full 4-digit years
    years = _YEAR_RE.findall(block)
    if years:
        entry["year"] = years[-1]  # Last year = graduation

    # Extract GPA
    gpa_match = _GPA_RE.search(block)
    if gpa_match:
        gpa_val = gpa_match.group(1) or gpa_match.group(2)
        if gpa_val:
            entry["gpa"] = gpa_val

    return entry
