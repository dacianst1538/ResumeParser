import re
from typing import List, Dict, Optional

_PIN_RE = re.compile(r"\b\d{5,6}\b")

_ADDRESS_LABELS = re.compile(
    r"^(?:address|location|residing|residence|city|state|pin\s*code|zip\s*code|postal)\s*[:\-–—]\s*",
    re.IGNORECASE
)

_ADDRESS_INDICATORS = re.compile(
    r"(?:address|location|residing|residence|city|state|pin\s*code|zip\s*code|postal)\s*[:\-–—]?\s*",
    re.IGNORECASE
)

_US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC"
}

_INDIAN_STATES = {
    "andhra pradesh","arunachal pradesh","assam","bihar","chhattisgarh","goa",
    "gujarat","haryana","himachal pradesh","jharkhand","karnataka","kerala",
    "madhya pradesh","maharashtra","manipur","meghalaya","mizoram","nagaland",
    "odisha","punjab","rajasthan","sikkim","tamil nadu","telangana","tripura",
    "uttar pradesh","uttarakhand","west bengal","delhi","chandigarh","puducherry",
}

_INDIAN_CITIES = {
    "mumbai","delhi","bangalore","bengaluru","hyderabad","ahmedabad","chennai",
    "kolkata","pune","jaipur","lucknow","kanpur","nagpur","indore","thane",
    "bhopal","visakhapatnam","patna","vadodara","ghaziabad","ludhiana","agra",
    "nashik","faridabad","meerut","rajkot","varanasi","srinagar","aurangabad",
    "dhanbad","amritsar","navi mumbai","allahabad","ranchi","howrah","coimbatore",
    "jabalpur","gwalior","vijayawada","jodhpur","madurai","raipur","kochi",
    "chandigarh","mysore","mysuru","noida","gurgaon","gurugram","trivandrum",
    "thiruvananthapuram","salem","tiruchirappalli","bhubaneswar","dehradun",
    "new york","los angeles","chicago","houston","san francisco","seattle",
    "boston","austin","denver","atlanta","dallas","san jose","portland",
}

_COUNTRY_RE = re.compile(
    r"\b(?:India|USA|United States|United Kingdom|UK|Canada|Australia|Germany|Singapore|UAE|Dubai)\b",
    re.IGNORECASE
)


def _strip_label(line: str) -> str:
    """Remove address/location labels from the start of a line."""
    return _ADDRESS_LABELS.sub("", line).strip()


def _score_address_line(line: str) -> float:
    score = 0.0
    # Score on the cleaned text (without label)
    cleaned = _strip_label(line)
    lower = cleaned.lower().strip()

    if _PIN_RE.search(cleaned):
        score += 0.4

    for city in _INDIAN_CITIES:
        if city in lower:
            score += 0.3
            break

    for state in _INDIAN_STATES:
        if state in lower:
            score += 0.2
            break

    words_upper = cleaned.split()
    for w in words_upper:
        if w.upper().rstrip(".,") in _US_STATES:
            score += 0.2
            break

    if _COUNTRY_RE.search(cleaned):
        score += 0.2

    if _ADDRESS_INDICATORS.search(line):
        score += 0.3

    if cleaned.count(",") >= 1:
        score += 0.15

    return min(score, 1.0)


def extract_addresses(text: str) -> List[Dict]:
    addresses = []
    lines = text.split("\n")

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or len(stripped) < 5:
            continue

        score = _score_address_line(stripped)
        if score >= 0.4:
            # Parse the CLEANED line (label stripped)
            cleaned = _strip_label(stripped)
            addr = _parse_address_line(cleaned)
            addr["_confidence"] = round(score, 2)
            addresses.append(addr)

    if len(addresses) > 1:
        addresses.sort(key=lambda a: a.get("_confidence", 0), reverse=True)

    return addresses[:2]


def _parse_address_line(line: str) -> Dict:
    addr: Dict[str, Optional[str]] = {
        "street": None,
        "city": None,
        "state": None,
        "zip": None,
        "country": None,
    }

    lower = line.lower()

    pin_match = _PIN_RE.search(line)
    if pin_match:
        addr["zip"] = pin_match.group(0)

    country_match = _COUNTRY_RE.search(line)
    if country_match:
        addr["country"] = country_match.group(0)

    for city in _INDIAN_CITIES:
        if city in lower:
            addr["city"] = city.title()
            break

    for state in _INDIAN_STATES:
        if state in lower:
            addr["state"] = state.title()
            break

    if not addr["state"]:
        for w in line.split():
            if w.upper().rstrip(".,") in _US_STATES:
                addr["state"] = w.upper().rstrip(".,")
                break

    # Whatever is left after removing known parts is street
    remaining = line
    for val in [addr["zip"], addr["city"], addr["state"], addr["country"]]:
        if val:
            remaining = re.sub(re.escape(val), "", remaining, flags=re.IGNORECASE)
    remaining = re.sub(r"[,\s]+$", "", remaining).strip()
    remaining = re.sub(r"^[,\s]+", "", remaining).strip()
    if remaining and len(remaining) > 3:
        addr["street"] = remaining
    
    return addr
