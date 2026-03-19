import re
from typing import List, Dict

# Words that indicate this is NOT a project but a job/role
_NON_PROJECT_RE = re.compile(
    r"^(?:intern(?:ship)?|data\s+analy(?:st|sis)|software\s+(?:engineer|developer)|"
    r"web\s+developer|full\s*stack|front\s*end|back\s*end|"
    r"(?:senior|junior|lead)\s+\w+|trainee|associate|"
    r"name\s*:|phone\s*:|email\s*:|location\s*:)\s*$",
    re.IGNORECASE
)


def extract_certifications(section_text: str) -> List[str]:
    if not section_text or not section_text.strip():
        return []

    certs = []
    lines = section_text.strip().split("\n")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Remove bullet markers
        cleaned = re.sub(r"^[\s•●▪◦\-\*→\d\.]+\s*", "", stripped).strip()
        if not cleaned or len(cleaned) < 3:
            continue

        # Skip lines that are just dates or very short
        if re.fullmatch(r"[\d\s/\-\.]+", cleaned):
            continue

        # Skip lines that look like contact info from another resume
        if re.match(r"^(?:Name|Phone|Email|Location|LinkedIn|GitHub)\s*:", cleaned, re.IGNORECASE):
            continue

        # Skip lines that look like resume boundaries
        if re.match(r"^(?:Dummy\s+Resume|Resume\s*\d)", cleaned, re.IGNORECASE):
            continue

        certs.append(cleaned)

    return certs


def extract_projects(section_text: str) -> List[Dict]:
    if not section_text or not section_text.strip():
        return []

    projects = []
    lines = section_text.strip().split("\n")
    current_project: Dict = {}
    description_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_project:
                current_project["description"] = "\n".join(description_lines).strip() or None
                projects.append(current_project)
                current_project = {}
                description_lines = []
            continue

        is_bullet = stripped.startswith(("•", "-", "●", "▪", "◦", "*", "→"))
        is_short = len(stripped) < 80

        # Skip lines that look like job titles, not projects
        if _NON_PROJECT_RE.match(stripped):
            continue

        # Skip contact info lines
        if re.match(r"^(?:Name|Phone|Email|Location|LinkedIn|GitHub)\s*:", stripped, re.IGNORECASE):
            continue

        if not is_bullet and is_short and not current_project:
            current_project = _parse_project_title(stripped)
            description_lines = []
        elif not is_bullet and is_short and current_project:
            if not stripped.lower().startswith(("developed", "built", "created", "implemented", "designed", "used", "utilized", "responsible", "worked", "performed", "assisted", "learned", "contributed", "added")):
                current_project["description"] = "\n".join(description_lines).strip() or None
                projects.append(current_project)
                current_project = _parse_project_title(stripped)
                description_lines = []
            else:
                description_lines.append(stripped)
        elif current_project:
            cleaned = re.sub(r"^[\s•●▪◦\-\*→]+\s*", "", stripped).strip()
            if cleaned:
                description_lines.append(cleaned)

    if current_project:
        current_project["description"] = "\n".join(description_lines).strip() or None
        projects.append(current_project)

    return projects


def _parse_project_title(line: str) -> Dict:
    project: Dict = {
        "name": None,
        "technologies": None,
        "description": None,
    }

    pipe_match = re.match(r"^(.+?)\s*[\|–—]\s*(.+)$", line)
    paren_match = re.match(r"^(.+?)\s*\((.+?)\)\s*$", line)

    if pipe_match:
        project["name"] = pipe_match.group(1).strip()
        project["technologies"] = pipe_match.group(2).strip()
    elif paren_match:
        project["name"] = paren_match.group(1).strip()
        project["technologies"] = paren_match.group(2).strip()
    else:
        cleaned = re.sub(r"^[\s•●▪◦\-\*→\d\.]+\s*", "", line).strip()
        # Remove trailing date ranges like "2024 - 2025"
        cleaned = re.sub(r"\s*,?\s*\d{4}\s*[\-–—]\s*\d{4}\s*$", "", cleaned).strip()
        cleaned = re.sub(r"\s*,?\s*\d{4}\s*$", "", cleaned).strip()
        project["name"] = cleaned if cleaned else line.strip()

    return project
