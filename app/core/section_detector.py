import re
from typing import Dict, List, Tuple

SECTION_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("summary", re.compile(
        r"^(?:professional\s+)?(?:summary|profile|objective|about\s*me|career\s+(?:summary|objective|profile)|executive\s+summary)\s*:?\s*$",
        re.IGNORECASE
    )),
    ("education", re.compile(
        r"^(?:education|academic|qualification|academics|educational\s+(?:background|qualification|details))\s*:?\s*$",
        re.IGNORECASE
    )),
    ("work_experience", re.compile(
        r"^(?:(?:work|professional|employment|career)\s+)?(?:experience|history|background)|(?:experience|internship)\s*:?\s*$",
        re.IGNORECASE
    )),
    ("skills", re.compile(
        r"^(?:(?:technical|key|core|professional|primary)\s+)?skills(?:\s+(?:&|and)\s+(?:competencies|expertise|tools))?|(?:technologies|tech\s+stack|tools?\s*(?:&|and)?\s*technologies)\s*:?\s*$",
        re.IGNORECASE
    )),
    ("certifications", re.compile(
        r"^(?:certifications?|licenses?(?:\s*(?:&|and)\s*certifications?)?|professional\s+certifications?|accreditations?)\s*:?\s*$",
        re.IGNORECASE
    )),
    ("projects", re.compile(
        r"^(?:(?:key|major|personal|academic|notable)\s+)?projects?\s*:?\s*$",
        re.IGNORECASE
    )),
    ("awards", re.compile(
        r"^(?:awards?|honors?|achievements?|accomplishments?)(?:\s*(?:&|and)\s*(?:awards?|honors?|achievements?))?\s*:?\s*$",
        re.IGNORECASE
    )),
    ("languages", re.compile(
        r"^(?:languages?\s*(?:known|spoken|proficiency)?)\s*:?\s*$",
        re.IGNORECASE
    )),
    ("interests", re.compile(
        r"^(?:interests?|hobbies?|extra[\s-]?curricular(?:\s+activities)?)\s*:?\s*$",
        re.IGNORECASE
    )),
    ("references", re.compile(
        r"^(?:references?)\s*:?\s*$",
        re.IGNORECASE
    )),
    ("declaration", re.compile(
        r"^(?:declaration)\s*:?\s*$",
        re.IGNORECASE
    )),
    ("activities", re.compile(
        r"^(?:activities|extra[\s-]?curricular|volunteer(?:ing)?|community)\s*:?\s*$",
        re.IGNORECASE
    )),
]

# Detect new resume boundary — "Dummy Resume 2", "Name: Xyz", or a line that looks like a new person's header
_RESUME_BOUNDARY_RE = re.compile(
    r"^(?:dummy\s+resume|resume\s*\d|---+|===+)\s*\d*\s*$",
    re.IGNORECASE
)

_NEW_PERSON_HEADER_RE = re.compile(
    r"^Name\s*:\s*.+",
    re.IGNORECASE
)


def _is_resume_boundary(line: str, prev_sections: List[str]) -> bool:
    stripped = line.strip()
    if _RESUME_BOUNDARY_RE.match(stripped):
        return True
    # "Name: Xyz" appearing AFTER we've already parsed sections = new resume
    if _NEW_PERSON_HEADER_RE.match(stripped) and len(prev_sections) > 2:
        return True
    return False


def detect_sections(text: str) -> Dict[str, str]:
    lines = text.split("\n")
    sections: Dict[str, str] = {}
    current_section = "header"
    current_lines: List[str] = []
    detected_sections: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            current_lines.append("")
            continue

        # Check for multi-resume boundary — stop parsing here
        if _is_resume_boundary(stripped, detected_sections):
            if current_lines or current_section != "header":
                sections[current_section] = "\n".join(current_lines).strip()
            break

        matched_section = None
        for section_name, pattern in SECTION_PATTERNS:
            if pattern.match(stripped):
                matched_section = section_name
                break

        # Detect inline headers like "SKILLS:" with content after
        if not matched_section and len(stripped) < 60:
            for section_name, pattern in SECTION_PATTERNS:
                header_match = re.match(
                    r"^(" + pattern.pattern.lstrip("^").rstrip(r"\s*:?\s*$") + r")\s*[:\-–—]\s*(.+)$",
                    stripped, re.IGNORECASE
                )
                if header_match:
                    matched_section = section_name
                    remaining = header_match.group(2).strip() if header_match.lastindex >= 2 else ""
                    if current_lines or current_section != "header":
                        sections[current_section] = "\n".join(current_lines).strip()
                        detected_sections.append(current_section)
                    current_section = matched_section
                    current_lines = [remaining] if remaining else []
                    matched_section = None
                    break

        if matched_section:
            if current_lines or current_section != "header":
                sections[current_section] = "\n".join(current_lines).strip()
                detected_sections.append(current_section)
            current_section = matched_section
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections[current_section] = "\n".join(current_lines).strip()

    return sections
