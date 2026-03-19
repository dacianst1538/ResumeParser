import re
from typing import List, Dict, Optional

_MONTH_NAMES = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"

_DATE_RANGE_RE = re.compile(
    rf"({_MONTH_NAMES}[\s,.']*\d{{2,4}}|\d{{1,2}}[/\-.]?\d{{2,4}}|\d{{4}})"
    r"\s*[\-–—]+\s*"
    rf"({_MONTH_NAMES}[\s,.']*\d{{2,4}}|\d{{1,2}}[/\-.]?\d{{2,4}}|\d{{4}}|Present|Current|Till\s*(?:Date|Now|Present))",
    re.IGNORECASE
)

_TITLE_PATTERNS = re.compile(
    r"(?:"
    r"(?:Senior|Junior|Lead|Principal|Staff|Chief|Head|Associate|Assistant|Deputy|Vice|Managing|Executive)?\s*"
    r"(?:Software|Web|Full[\s\-]?Stack|Front[\s\-]?End|Back[\s\-]?End|Mobile|Cloud|Data|ML|AI|DevOps|QA|Test|UI/?UX|Product|Project|Program|Business|System|Network|Database|Security|Solutions?)?\s*"
    r"(?:Engineer|Developer|Architect|Analyst|Manager|Consultant|Designer|Administrator|Specialist|Coordinator|Director|Officer|Scientist|Researcher|Tester|Lead|Trainee)"
    r"|Intern(?:ship)?"
    r"|CTO|CEO|CFO|COO|CIO|VP|SVP|AVP"
    r")",
    re.IGNORECASE
)

_COMPANY_SUFFIXES = re.compile(
    r"\b(?:Inc\.?|LLC|Ltd\.?|Pvt\.?|Private|Limited|Corp(?:oration)?\.?|Co\.?|Group|Technologies|Tech|Solutions|Services|Consulting|Systems|Software|Labs?|Global|International)\b",
    re.IGNORECASE
)

_TITLE_AT_COMPANY_RE = re.compile(
    r"^(.+?)\s+(?:at|@)\s+(.+?)$",
    re.IGNORECASE
)

_BULLET_STARTS = ("•", "-", "●", "▪", "◦", "*", "→", "–")


def _is_bullet(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith(_BULLET_STARTS) or bool(re.match(r"^\d+[\.\)]\s", stripped))


def extract_work_experience(section_text: str) -> List[Dict]:
    if not section_text or not section_text.strip():
        return []

    lines = section_text.strip().split("\n")
    entries: List[Dict] = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        if _is_bullet(line):
            # Append to last entry as description
            if entries:
                cleaned = re.sub(r"^[\s•●▪◦\-\*→–]+\s*", "", line).strip()
                if cleaned:
                    if entries[-1]["description"]:
                        entries[-1]["description"] += "\n" + cleaned
                    else:
                        entries[-1]["description"] = cleaned
            i += 1
            continue

        # Try to parse as a new entry (may consume multiple lines)
        entry, consumed = _try_parse_entry(lines, i)
        if entry and (entry.get("title") or entry.get("company") or entry.get("startDate")):
            entries.append(entry)
            i += consumed
        elif entries:
            # Not a new entry — append as description to last
            cleaned = re.sub(r"^[\s•●▪◦\-\*→–]+\s*", "", line).strip()
            if cleaned:
                if entries[-1]["description"]:
                    entries[-1]["description"] += "\n" + cleaned
                else:
                    entries[-1]["description"] = cleaned
            i += 1
        else:
            i += 1

    return entries


def _try_parse_entry(lines: List[str], idx: int) -> tuple:
    """Try to parse an experience entry starting at idx. Returns (entry_dict, lines_consumed)."""
    line = lines[idx].strip()
    if not line:
        return None, 1

    entry: Dict = {
        "company": None,
        "title": None,
        "startDate": None,
        "endDate": None,
        "location": None,
        "description": None,
    }

    has_date = _DATE_RANGE_RE.search(line)
    has_title = _TITLE_PATTERNS.search(line)
    has_company = _COMPANY_SUFFIXES.search(line)
    has_at = _TITLE_AT_COMPANY_RE.match(line)

    # ── Case 1: Date range on this line ──
    if has_date:
        entry["startDate"] = has_date.group(1).strip()
        entry["endDate"] = has_date.group(2).strip()
        text_part = (line[:has_date.start()] + line[has_date.end():]).strip().strip(",").strip()
        if text_part:
            _extract_title_company(text_part, entry)

        # If no title/company found on this line, check previous context
        # (sometimes company is on the line above the date)
        return entry, 1

    # ── Case 2: Title/Company line, date on next line ──
    if has_title or has_company or has_at:
        consumed = 1

        # Check next line for date range
        if idx + 1 < len(lines):
            next_line = lines[idx + 1].strip()
            next_date = _DATE_RANGE_RE.search(next_line)
            if next_date:
                entry["startDate"] = next_date.group(1).strip()
                entry["endDate"] = next_date.group(2).strip()
                remaining = (next_line[:next_date.start()] + next_line[next_date.end():]).strip().strip(",").strip()
                if remaining and not _TITLE_PATTERNS.search(remaining):
                    entry["location"] = remaining
                consumed = 2

        _extract_title_company(line, entry)

        # If we only got company (no title), check if next non-date line has title
        if entry["company"] and not entry["title"] and idx + consumed < len(lines):
            peek = lines[idx + consumed].strip()
            if _TITLE_PATTERNS.search(peek) and not _is_bullet(peek):
                entry["title"] = peek.strip()
                consumed += 1

        # If we only got title (no company), check if next non-date line has company
        if entry["title"] and not entry["company"] and idx + consumed < len(lines):
            peek = lines[idx + consumed].strip()
            if _COMPANY_SUFFIXES.search(peek) and not _is_bullet(peek) and not _DATE_RANGE_RE.search(peek):
                entry["company"] = peek.strip()
                consumed += 1

        return entry, consumed

    # ── Case 3: Company name alone on a line (no title pattern, but has company suffix) ──
    # Check if next line has a title or date
    if idx + 1 < len(lines):
        next_line = lines[idx + 1].strip()
        if _TITLE_PATTERNS.search(next_line) or _DATE_RANGE_RE.search(next_line):
            entry["company"] = line
            consumed = 1

            if _TITLE_PATTERNS.search(next_line) and not _DATE_RANGE_RE.search(next_line):
                entry["title"] = next_line.strip()
                consumed = 2
                # Check line after for date
                if idx + 2 < len(lines):
                    date_line = lines[idx + 2].strip()
                    date_match = _DATE_RANGE_RE.search(date_line)
                    if date_match:
                        entry["startDate"] = date_match.group(1).strip()
                        entry["endDate"] = date_match.group(2).strip()
                        consumed = 3
            elif _DATE_RANGE_RE.search(next_line):
                date_match = _DATE_RANGE_RE.search(next_line)
                entry["startDate"] = date_match.group(1).strip()
                entry["endDate"] = date_match.group(2).strip()
                consumed = 2

            return entry, consumed

    return None, 1


def _extract_title_company(text: str, entry: Dict):
    text = text.strip().rstrip(",").strip()
    if not text:
        return

    # Try "Title at/@ Company" pattern first
    at_match = _TITLE_AT_COMPANY_RE.match(text)
    if at_match:
        entry["title"] = at_match.group(1).strip()
        entry["company"] = at_match.group(2).strip()
        return

    # Try splitting by | separator
    parts = re.split(r"\s*[\|]\s*", text)
    if len(parts) == 1:
        # Try comma split only if one part has title and other doesn't
        comma_parts = re.split(r"\s*,\s*", text, maxsplit=1)
        if len(comma_parts) == 2:
            parts = comma_parts

    if len(parts) >= 2:
        for part in parts:
            part = part.strip()
            if _TITLE_PATTERNS.search(part) and not entry["title"]:
                entry["title"] = part
            elif not entry["company"]:
                entry["company"] = part

        if not entry["title"] and not entry["company"]:
            entry["title"] = parts[0].strip()
            entry["company"] = parts[1].strip() if len(parts) > 1 else None
        return

    # Single chunk — find title pattern
    title_match = _TITLE_PATTERNS.search(text)
    if title_match:
        entry["title"] = title_match.group(0).strip()
        remaining = (text[:title_match.start()] + text[title_match.end():]).strip()
        remaining = re.sub(r"^[\s,\-–—\|@]+", "", remaining).strip()
        remaining = re.sub(r"[\s,\-–—\|@]+$", "", remaining).strip()
        if remaining and len(remaining) > 2:
            entry["company"] = remaining
        return

    # No title pattern — might be just a company name
    if _COMPANY_SUFFIXES.search(text):
        entry["company"] = text
    elif len(text) < 50:
        # Short text without title pattern — could be company name
        entry["company"] = text
