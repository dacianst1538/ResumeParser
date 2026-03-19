import json
from app.core.parser_engine import parse_resume

resume_text = """John Doe
johndoe@gmail.com | +91-9876543210 | linkedin.com/in/johndoe
Bangalore, Karnataka, India

Summary
Full Stack Developer with 5 years of experience in building web applications.

Experience
Senior Software Engineer at TCS Ltd
Jan 2021 - Present
- Built microservices using Python and FastAPI
- Deployed on AWS using Docker and Kubernetes

Software Developer at Infosys Ltd
Jun 2018 - Dec 2020
- Developed REST APIs using Java Spring Boot
- Worked with PostgreSQL and Redis

Education
B.Tech in Computer Science
Indian Institute of Technology, Delhi
2018
CGPA: 8.5/10

Skills
Python, Java, JavaScript, React, FastAPI, Spring Boot, Docker, Kubernetes, AWS, PostgreSQL, Redis, Git

Certifications
AWS Certified Solutions Architect
Kubernetes Administrator (CKA)

Projects
E-Commerce Platform | React, Node.js, MongoDB
Built a full-stack e-commerce app with payment integration"""

result = parse_resume(resume_text)
print(json.dumps(result, indent=2, ensure_ascii=False))
