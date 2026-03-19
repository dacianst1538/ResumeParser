# Resume Parser API

A fast, lightweight resume parser built with Python and FastAPI. It extracts structured data from raw resume text using regex patterns and heuristics — no ML models, no external AI APIs.

Built this as a backend microservice that takes plain text resumes and returns clean JSON with contact info, education, work experience, skills, and more.

## What It Extracts

- **Name** — from the top of the resume using multiple detection strategies
- **Emails, Phone Numbers, Websites** — regex-based extraction from the header
- **Date of Birth** — if labeled in the resume
- **Addresses** — scored against known Indian and US cities, states, and PIN/ZIP codes
- **Summary / Objective** — detected by section headers
- **Education** — degree, institution, year, GPA, field of study
- **Work Experience** — company, job title, date range, description
- **Skills** — section-based parsing + full-text scan against 200+ known skills
- **Certifications** — listed certifications
- **Projects** — project name, technologies used, description

Every field comes with a **confidence score** (0.0 to 1.0) so the consumer knows how reliable each extraction is.

## Tech Stack

- **Python 3.11+**
- **FastAPI** — async REST API framework
- **Uvicorn** — ASGI server
- **Pydantic** — request/response validation
- **Regex + Heuristics** — all parsing is rule-based, zero ML dependencies

## Project Structure

```
ResumeParser/
├── main.py                        # FastAPI app, endpoints, server startup
├── pyproject.toml                 # Dependencies and project config
├── run_server.bat                 # Quick-start script (Windows)
├── test_parser.py                 # Manual smoke test with sample resume
├── app/
│   ├── core/
│   │   ├── config.py              # Server settings (host, port, log level)
│   │   ├── parser_engine.py       # Main orchestrator — runs all extractors
│   │   └── section_detector.py    # Splits resume into named sections
│   └── extractors/
│       ├── name_extractor.py      # Candidate name extraction
│       ├── contact_extractor.py   # Emails, phones, URLs, DOB
│       ├── address_extractor.py   # Physical address parsing
│       ├── education_extractor.py # Degree, institution, GPA, year
│       ├── experience_extractor.py# Job title, company, dates, bullets
│       ├── skills_extractor.py    # Skills (section + full-text keyword scan)
│       └── section_extractor.py   # Certifications and projects
```

## How It Works

1. **Section Detection** — scans the resume line by line and splits it into sections (header, summary, education, experience, skills, etc.) using regex pattern matching on section headers.

2. **Extraction Pipeline** — the parser engine runs 10 extractors in sequence, each focused on one data type. Every extractor receives only its relevant section text.

3. **Confidence Scoring** — each extractor returns a confidence score. The engine computes a weighted overall confidence where name, emails, skills, and experience are weighted highest.

4. **JSON Response** — returns all extracted data, per-field confidence scores, overall confidence, and which sections were detected.

## Getting Started

### Install Dependencies

```bash
pip install -e .
```

### Start the Server

```bash
python main.py
```

Server runs on `http://localhost:2700`

### API Endpoints

**Parse Resume**

```
POST /parse-resume
```

Request body:
```json
{
  "resume_text": "John Doe\njohndoe@gmail.com | +91-9876543210\n\nSummary\nFull Stack Developer with 5 years of experience..."
}
```

Response:
```json
{
  "success": true,
  "data": {
    "name": "John Doe",
    "emails": ["johndoe@gmail.com"],
    "phoneNumbers": ["+91-9876543210"],
    "websites": [],
    "dateOfBirth": null,
    "addresses": [],
    "summary": "Full Stack Developer with 5 years of experience...",
    "education": [],
    "workExperience": [],
    "skills": ["Python", "FastAPI", "React"],
    "certifications": [],
    "projects": []
  },
  "confidence": {
    "name": 0.88,
    "emails": 0.99,
    "phoneNumbers": 0.95,
    "skills": 0.90
  },
  "overall_confidence": 0.85,
  "sections_detected": ["header", "summary", "skills"]
}
```

**Health Check**

```
GET /health
```

Returns `{"status": "ok", "version": "1.0.0"}`

### API Docs

FastAPI auto-generates interactive docs at `http://localhost:2700/docs`

## Run the Test

```bash
python test_parser.py
```

Parses a sample resume and prints the full JSON output to verify everything works.
