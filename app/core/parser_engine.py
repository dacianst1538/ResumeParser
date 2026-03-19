from typing import Dict, Any

from app.core.section_detector import detect_sections
from app.extractors.contact_extractor import extract_contacts
from app.extractors.name_extractor import extract_name
from app.extractors.address_extractor import extract_addresses
from app.extractors.education_extractor import extract_education
from app.extractors.experience_extractor import extract_work_experience
from app.extractors.skills_extractor import extract_skills_from_section, extract_skills_from_full_text
from app.extractors.section_extractor import extract_certifications, extract_projects


def parse_resume(resume_text: str) -> Dict[str, Any]:
    if not resume_text or not resume_text.strip():
        return {
            "success": False,
            "error": "Empty resume text",
            "data": {},
            "confidence": {},
        }

    try:
        # 1. Detect sections
        sections = detect_sections(resume_text)
        header = sections.get("header", "")

        # 2. Extract contacts (regex — from full text)
        contacts = extract_contacts(resume_text)

        # 3. Extract name (heuristic — from header)
        name, name_confidence = extract_name(header if header else resume_text)

        # 4. Extract addresses (heuristic — from header)
        addresses = extract_addresses(header if header else resume_text[:1000])
        addr_confidence = 0.0
        clean_addresses = []
        for addr in addresses:
            addr_confidence = addr.pop("_confidence", 0.75)
            clean_addresses.append(addr)

        # 5. Extract summary
        summary = sections.get("summary", None)
        summary_confidence = 0.88 if summary else 0.0

        # 6. Extract education
        edu_section = sections.get("education", "")
        education = extract_education(edu_section)
        education_confidence = 0.88 if education else 0.0

        # 7. Extract work experience
        exp_section = sections.get("work_experience", "")
        work_experience = extract_work_experience(exp_section)
        experience_confidence = 0.83 if work_experience else 0.0

        # 8. Extract skills (section-based + full-text keyword scan)
        skills_section = sections.get("skills", "")
        section_skills = extract_skills_from_section(skills_section)
        fulltext_skills = extract_skills_from_full_text(resume_text)

        # Merge: section skills first, then add any from full-text not already found
        seen_lower = {s.lower() for s in section_skills}
        all_skills = list(section_skills)
        for s in fulltext_skills:
            if s.lower() not in seen_lower:
                seen_lower.add(s.lower())
                all_skills.append(s)

        skills_confidence = 0.90 if section_skills else (0.75 if fulltext_skills else 0.0)

        # 9. Extract certifications
        cert_section = sections.get("certifications", "")
        certifications = extract_certifications(cert_section)
        cert_confidence = 0.85 if certifications else 0.0

        # 10. Extract projects
        proj_section = sections.get("projects", "")
        projects = extract_projects(proj_section)
        proj_confidence = 0.83 if projects else 0.0

        # Build output matching backend's expected format
        data = {
            "name": name,
            "emails": contacts["emails"],
            "phoneNumbers": contacts["phoneNumbers"],
            "websites": contacts["websites"],
            "dateOfBirth": contacts["dateOfBirth"],
            "addresses": clean_addresses,
            "summary": summary,
            "education": education,
            "workExperience": work_experience,
            "skills": all_skills,
            "certifications": certifications,
            "projects": projects,
        }

        confidence = {
            "name": round(name_confidence, 2),
            "emails": contacts["confidence"]["emails"],
            "phoneNumbers": contacts["confidence"]["phoneNumbers"],
            "websites": contacts["confidence"]["websites"],
            "dateOfBirth": contacts["confidence"]["dateOfBirth"],
            "addresses": round(addr_confidence, 2) if clean_addresses else 0.0,
            "summary": summary_confidence,
            "education": education_confidence,
            "workExperience": experience_confidence,
            "skills": skills_confidence,
            "certifications": cert_confidence,
            "projects": proj_confidence,
        }

        # Overall confidence = weighted average
        weights = {
            "name": 3, "emails": 3, "phoneNumbers": 2, "skills": 3,
            "workExperience": 3, "education": 2, "summary": 1,
            "addresses": 1, "websites": 1, "dateOfBirth": 0.5,
            "certifications": 1, "projects": 1,
        }
        total_weight = sum(weights.values())
        overall = sum(confidence.get(k, 0) * w for k, w in weights.items()) / total_weight

        return {
            "success": True,
            "data": data,
            "confidence": confidence,
            "overall_confidence": round(overall, 2),
            "sections_detected": list(sections.keys()),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": {},
            "confidence": {},
        }
