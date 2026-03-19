import re
from typing import List, Set

KNOWN_SKILLS: Set[str] = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl",
    "dart", "lua", "haskell", "elixir", "clojure", "groovy", "objective-c",
    "visual basic", "vb.net", "assembly", "fortran", "cobol", "shell", "bash",
    "powershell", "sql", "plsql", "pl/sql", "t-sql", "nosql",

    # Web Frameworks
    "react", "reactjs", "react.js", "angular", "angularjs", "vue", "vuejs", "vue.js",
    "next.js", "nextjs", "nuxt.js", "nuxtjs", "svelte", "ember.js",
    "django", "flask", "fastapi", "spring", "spring boot", "springboot",
    "express", "express.js", "expressjs", "node.js", "nodejs", "nest.js", "nestjs",
    "rails", "ruby on rails", "laravel", "symfony", "asp.net", ".net", ".net core",
    "blazor", "gin", "fiber", "echo",

    # Mobile
    "react native", "flutter", "ionic", "xamarin", "swiftui", "android", "ios",
    "kotlin multiplatform",

    # Databases
    "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "sqlite", "oracle", "sql server", "mssql",
    "mariadb", "couchdb", "neo4j", "firebase", "supabase", "cockroachdb",
    "influxdb", "timescaledb",

    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "amazon web services",
    "docker", "kubernetes", "k8s", "terraform", "ansible", "puppet", "chef",
    "jenkins", "github actions", "gitlab ci", "circleci", "travis ci",
    "cloudformation", "pulumi", "vagrant",
    "ec2", "s3", "lambda", "ecs", "eks", "fargate", "rds", "sqs", "sns",
    "cloudfront", "route53", "api gateway", "step functions",
    "azure devops", "azure functions", "azure pipelines",

    # Data & ML
    "pandas", "numpy", "scipy", "scikit-learn", "sklearn", "tensorflow",
    "pytorch", "keras", "opencv", "nltk", "spacy", "hugging face", "transformers",
    "spark", "pyspark", "hadoop", "hive", "kafka", "airflow", "dbt",
    "tableau", "power bi", "looker", "grafana", "matplotlib", "seaborn", "plotly",
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "data science", "data engineering", "data analysis",
    "etl", "data pipeline", "data warehouse", "data lake",
    "llm", "generative ai", "rag", "langchain", "openai",

    # Tools & Platforms
    "git", "github", "gitlab", "bitbucket", "svn",
    "jira", "confluence", "trello", "asana", "notion",
    "linux", "unix", "windows server", "macos",
    "nginx", "apache", "iis", "tomcat",
    "rabbitmq", "celery", "zeromq",
    "graphql", "rest", "restful", "soap", "grpc", "websocket",
    "oauth", "jwt", "saml", "openid",
    "webpack", "vite", "babel", "eslint", "prettier",
    "jest", "mocha", "pytest", "junit", "selenium", "cypress", "playwright",
    "postman", "swagger", "openapi",
    "vs code", "visual studio", "intellij", "eclipse", "pycharm",
    "ms excel", "excel", "word", "powerpoint",

    # Methodologies
    "agile", "scrum", "kanban", "waterfall", "devops", "ci/cd", "cicd",
    "tdd", "bdd", "microservices", "monolith", "serverless", "event-driven",
    "design patterns", "solid", "oop", "functional programming",

    # Other
    "html", "html5", "css", "css3", "sass", "scss", "less", "tailwind",
    "tailwindcss", "bootstrap", "material ui", "chakra ui",
    "figma", "sketch", "adobe xd", "photoshop", "illustrator",
    "xml", "json", "yaml", "toml", "csv", "protobuf",
    "blockchain", "solidity", "web3", "ethereum",
    "unity", "unreal engine", "godot",
}

_NORMALIZED_SKILLS = {s.lower(): s for s in KNOWN_SKILLS}

# Category label prefixes to strip: "Programming:", "Libraries:", "Web Development:", etc.
_CATEGORY_PREFIX_RE = re.compile(
    r"^(?:programming(?:\s+languages?)?|languages?|web\s+(?:development|technologies)|"
    r"frameworks?|libraries?|databases?|tools?\s*(?:&|and)?\s*(?:platforms?|technologies)?|"
    r"analytics?|cloud|devops|data(?:bases?)?|frontend|backend|mobile|testing|"
    r"(?:version\s+)?control|ide|editors?|os|operating\s+systems?|"
    r"soft\s+skills|technical\s+skills|other)\s*[:\-–—]\s*",
    re.IGNORECASE
)


def _strip_category_prefix(text: str) -> str:
    """Remove category labels like 'Programming:' from skill tokens."""
    return _CATEGORY_PREFIX_RE.sub("", text).strip()


def extract_skills_from_section(section_text: str) -> List[str]:
    if not section_text or not section_text.strip():
        return []

    skills = []
    seen = set()

    # Process line by line first to handle "Category: skill1, skill2" format
    for line in section_text.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        # Strip category prefix from the line
        cleaned_line = _strip_category_prefix(line)

        # Split by common delimiters
        tokens = re.split(r"[,\|•●▪◦\*;]+", cleaned_line)

        for token in tokens:
            cleaned = token.strip().strip("()[]{}").strip()
            if not cleaned or len(cleaned) < 1 or len(cleaned) > 50:
                continue

            # Strip category prefix again (in case of "Programming: Python, Libraries: Pandas")
            cleaned = _strip_category_prefix(cleaned)
            if not cleaned:
                continue

            lower = cleaned.lower()

            # Direct match against known skills
            if lower in _NORMALIZED_SKILLS and lower not in seen:
                seen.add(lower)
                skills.append(_NORMALIZED_SKILLS[lower])
                continue

            # Check if token contains a known skill
            matched = False
            for known_lower, known_original in _NORMALIZED_SKILLS.items():
                if len(known_lower) >= 2 and re.search(r"\b" + re.escape(known_lower) + r"\b", lower):
                    if known_lower not in seen:
                        seen.add(known_lower)
                        skills.append(known_original)
                        matched = True

            # If not matched and looks like a skill (short, no filler words)
            if not matched and lower not in seen and 2 <= len(cleaned) <= 30:
                words = cleaned.split()
                skip_words = {
                    "and", "or", "the", "a", "an", "in", "of", "for", "with", "to",
                    "on", "at", "by", "is", "are", "was", "were", "etc", "including",
                    "such", "as", "using", "proficient", "experienced", "knowledge",
                    "familiar", "good", "strong", "excellent", "basic", "advanced",
                    "intermediate", "working", "hands", "exposure",
                }
                if not all(w.lower() in skip_words for w in words):
                    if len(words) <= 3:
                        seen.add(lower)
                        skills.append(cleaned)

    return skills


def extract_skills_from_full_text(text: str) -> List[str]:
    found = []
    seen = set()
    lower_text = text.lower()

    for known_lower, known_original in _NORMALIZED_SKILLS.items():
        if len(known_lower) >= 3 and known_lower not in seen:
            if re.search(r"\b" + re.escape(known_lower) + r"\b", lower_text):
                seen.add(known_lower)
                found.append(known_original)

    return found
