"""
AI Career Copilot
Day 31 - ATS Job Matching Engine

Compares a resume against a target job description.

Features:
- Skill matching
- Keyword matching
- Experience matching
- Skill normalization / aliases
- Missing skill detection
- Missing keyword detection
- Match explanation
- Recommended skills
- Overall Job Match Score

Run:
    python backend/job_matcher.py
"""

import json
import re
from typing import Any, Dict, List, Set


# ============================================================
# CONFIGURATION
# ============================================================

SKILL_ALIASES = {
    "rest apis": "rest api",
    "rest api": "rest api",
    "rest": "rest api",

    "apis": "api",
    "api development": "api",

    "ml": "machine learning",
    "machine-learning": "machine learning",

    "dl": "deep learning",
    "deep-learning": "deep learning",

    "ai": "artificial intelligence",
    "artificial intelligence": "artificial intelligence",

    "js": "javascript",
    "node": "node.js",
    "nodejs": "node.js",

    "postgres": "postgresql",
    "postgres sql": "postgresql",

    "aws cloud": "aws",
    "amazon web services": "aws",

    "gcp cloud": "gcp",
    "google cloud": "gcp",

    "docker container": "docker",
    "k8s": "kubernetes",

    "github": "github",
    "git hub": "github",
}


KNOWN_SKILLS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "c",
    "c++",
    "c#",
    "go",
    "rust",
    "php",

    "html",
    "css",
    "react",
    "angular",
    "vue",
    "node.js",

    "flask",
    "django",
    "fastapi",
    "spring",
    "express",

    "rest api",
    "api",

    "sql",
    "mysql",
    "postgresql",
    "mongodb",
    "sqlite",
    "redis",

    "git",
    "github",
    "gitlab",

    "docker",
    "kubernetes",

    "aws",
    "azure",
    "gcp",

    "cloud",

    "machine learning",
    "deep learning",
    "artificial intelligence",
    "tensorflow",
    "pytorch",
    "scikit-learn",

    "numpy",
    "pandas",

    "data science",
    "data analysis",

    "nlp",
    "computer vision",

    "software development",
    "backend",
    "frontend",
    "full stack",
    "full-stack",

    "deployment",
    "devops",
    "mlops",

    "linux",
    "restful api",
}


STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "for",
    "with",
    "from",
    "into",
    "onto",
    "using",
    "use",
    "used",
    "have",
    "has",
    "had",
    "this",
    "that",
    "these",
    "those",
    "are",
    "is",
    "be",
    "to",
    "of",
    "in",
    "on",
    "at",
    "by",
    "as",
    "we",
    "our",
    "you",
    "your",
    "they",
    "their",
    "will",
    "can",
    "should",
    "would",
    "could",
    "about",
    "within",
    "through",
    "than",
    "such",
    "its",
    "it",
    "job",
    "role",
    "work",
    "working",
    "candidate",
    "candidates",
    "preferred",
    "required",
    "requirements",
    "requirement",
    "responsibilities",
    "responsibility",
    "experience",
    "years",
    "year",
    "least",
    "plus",
    "strong",
    "good",
    "excellent",
    "knowledge",
    "skills",
    "skill",
}


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text: Any) -> str:
    """
    Normalize arbitrary text into clean lowercase searchable text.
    """

    if text is None:
        return ""

    text = str(text)

    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")

    text = text.lower()

    # Normalize common separators.
    text = text.replace("/", " ")
    text = text.replace("-", " ")

    # Remove punctuation but keep + and # for languages such as C++ / C#.
    text = re.sub(r"[^a-z0-9+#.\s]", " ", text)

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ============================================================
# CANONICAL SKILL
# ============================================================

def canonical_skill(skill: str) -> str:
    """
    Convert a skill into its canonical representation.
    """

    skill = normalize_text(skill)

    if not skill:
        return ""

    return SKILL_ALIASES.get(skill, skill)


# ============================================================
# SKILL EXTRACTION
# ============================================================

def extract_skills(text: str) -> List[str]:
    """
    Extract known technical skills from text.

    Multi-word skills are checked before single-word skills.
    """

    normalized = normalize_text(text)

    if not normalized:
        return []

    found: Set[str] = set()

    # Check longer skills first.
    sorted_skills = sorted(
        KNOWN_SKILLS,
        key=lambda value: len(value),
        reverse=True
    )

    for skill in sorted_skills:

        canonical = canonical_skill(skill)

        if not canonical:
            continue

        # Escape regex safely.
        pattern = re.escape(normalize_text(skill))

        # Word-boundary style matching.
        if re.search(rf"(?<!\w){pattern}(?!\w)", normalized):
            found.add(canonical)

    return sorted(found)


# ============================================================
# KEYWORD EXTRACTION
# ============================================================

def tokenize(text: str) -> List[str]:
    """
    Create clean tokens for keyword analysis.
    """

    normalized = normalize_text(text)

    if not normalized:
        return []

    tokens = normalized.split()

    clean_tokens = []

    for token in tokens:

        # Remove trailing dots.
        token = token.strip(".")

        if not token:
            continue

        if token in STOPWORDS:
            continue

        # Ignore extremely short generic tokens.
        if len(token) < 3:
            continue

        # Ignore pure numbers.
        if token.isdigit():
            continue

        clean_tokens.append(token)

    return clean_tokens


def extract_keywords(job_description: str) -> List[str]:
    """
    Extract useful job keywords.

    Priority:
    1. Known technical skills
    2. Useful multi-word phrases
    3. Meaningful single words

    Generic ATS noise is excluded.
    """

    normalized = normalize_text(job_description)

    if not normalized:
        return []

    keywords: Set[str] = set()

    # --------------------------------------------------------
    # 1. Known skills
    # --------------------------------------------------------

    for skill in extract_skills(normalized):
        keywords.add(skill)

    # --------------------------------------------------------
    # 2. Important multi-word phrases
    # --------------------------------------------------------

    phrase_patterns = [
        "machine learning",
        "deep learning",
        "artificial intelligence",
        "rest api",
        "software development",
        "backend development",
        "frontend development",
        "full stack",
        "data science",
        "data analysis",
        "cloud computing",
        "cloud deployment",
        "api development",
        "web development",
        "scalable systems",
        "scalable applications",
        "distributed systems",
        "system design",
        "continuous integration",
        "continuous deployment",
        "version control",
        "natural language processing",
        "computer vision",
    ]

    for phrase in phrase_patterns:

        phrase_normalized = normalize_text(phrase)

        if phrase_normalized in normalized:
            keywords.add(
                canonical_skill(phrase_normalized)
            )

    # --------------------------------------------------------
    # 3. Meaningful single-word keywords
    # --------------------------------------------------------

    tokens = tokenize(normalized)

    useful_context_words = {
        "deployment",
        "scalable",
        "systems",
        "applications",
        "backend",
        "frontend",
        "testing",
        "automation",
        "development",
        "engineering",
        "architecture",
        "integration",
        "security",
        "performance",
        "optimization",
        "database",
        "databases",
        "cloud",
        "debugging",
        "monitoring",
        "production",
        "analytics",
        "modeling",
        "models",
    }

    for token in tokens:

        if token in useful_context_words:
            keywords.add(token)

    return sorted(keywords)


# ============================================================
# KEYWORD MATCHING
# ============================================================

def match_keywords(
    resume_text: str,
    job_description: str
) -> Dict[str, Any]:
    """
    Compare job keywords against resume text.
    """

    resume_normalized = normalize_text(resume_text)

    job_keywords = extract_keywords(job_description)

    matched = []
    missing = []

    for keyword in job_keywords:

        keyword_normalized = normalize_text(keyword)

        if keyword_normalized in resume_normalized:
            matched.append(keyword)
        else:
            missing.append(keyword)

    return {
        "job_keywords": job_keywords,
        "matched_keywords": sorted(set(matched)),
        "missing_keywords": sorted(set(missing)),
    }


# ============================================================
# EXPERIENCE EXTRACTION
# ============================================================

def extract_experience_years(text: str) -> float:
    """
    Extract approximate years of professional experience.

    Examples detected:
        2 years experience
        2+ years
        1.5 years
        3 yrs
        6 months
        18 months

    Also handles ranges such as:
        2-3 years
    """

    normalized = normalize_text(text)

    if not normalized:
        return 0.0

    values = []

    # --------------------------------------------------------
    # Years
    # --------------------------------------------------------

    year_patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
        r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*(?:years?|yrs?)",
    ]

    for pattern in year_patterns:

        for match in re.finditer(pattern, normalized):

            try:

                if len(match.groups()) == 2:
                    first = float(match.group(1))
                    second = float(match.group(2))

                    values.append(
                        (first + second) / 2
                    )

                else:
                    values.append(
                        float(match.group(1))
                    )

            except (ValueError, TypeError):
                pass

    # --------------------------------------------------------
    # Months
    # --------------------------------------------------------

    month_pattern = r"(\d+(?:\.\d+)?)\s*(?:months?|mos?)"

    for match in re.finditer(month_pattern, normalized):

        try:

            months = float(match.group(1))
            values.append(months / 12)

        except (ValueError, TypeError):
            pass

    if not values:
        return 0.0

    # Avoid extreme accidental numbers.
    values = [
        value
        for value in values
        if 0 <= value <= 50
    ]

    if not values:
        return 0.0

    # Use the highest explicit experience value.
    return round(max(values), 1)


def extract_required_experience(job_description: str) -> float:
    """
    Extract required experience from a job description.

    Focuses on phrases such as:
        2 years experience
        minimum 3 years
        at least 2 years
        2+ years required
    """

    normalized = normalize_text(job_description)

    if not normalized:
        return 0.0

    patterns = [
        r"(?:minimum|at least|required|need|needs|requires|requiring)"
        r"\s*(?:of\s*)?"
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",

        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)"
        r"\s*(?:of\s*)?(?:relevant\s*)?"
        r"(?:experience|work experience|professional experience)",
    ]

    values = []

    for pattern in patterns:

        for match in re.finditer(pattern, normalized):

            try:
                values.append(float(match.group(1)))
            except (ValueError, TypeError):
                pass

    if not values:
        return 0.0

    return round(max(values), 1)


# ============================================================
# EXPERIENCE SCORE
# ============================================================

def calculate_experience_score(
    candidate_years: float,
    required_years: float
) -> Dict[str, Any]:
    """
    Calculate experience compatibility.

    If no experience is explicitly required:
        100

    If candidate has equal or greater experience:
        100

    Otherwise:
        proportional score.
    """

    candidate_years = max(float(candidate_years), 0.0)
    required_years = max(float(required_years), 0.0)

    if required_years <= 0:
        return {
            "score": 100,
            "candidate_years": candidate_years,
            "required_years": required_years,
            "status": "No specific experience requirement detected."
        }

    if candidate_years >= required_years:

        return {
            "score": 100,
            "candidate_years": candidate_years,
            "required_years": required_years,
            "status": "Candidate meets or exceeds the required experience."
        }

    if candidate_years <= 0:

        return {
            "score": 0,
            "candidate_years": 0.0,
            "required_years": required_years,
            "status": (
                "Required experience detected, "
                "but resume does not specify experience years."
            )
        }

    score = round(
        (candidate_years / required_years) * 100
    )

    score = max(0, min(100, score))

    return {
        "score": score,
        "candidate_years": candidate_years,
        "required_years": required_years,
        "status": (
            f"Candidate has about {candidate_years} years "
            f"against {required_years} required years."
        )
    }


# ============================================================
# SKILL MATCH
# ============================================================

def calculate_skill_match(
    resume_text: str,
    job_description: str
) -> Dict[str, Any]:
    """
    Compare normalized resume skills against required job skills.
    """

    resume_skills = extract_skills(resume_text)
    required_skills = extract_skills(job_description)

    resume_set = set(resume_skills)
    required_set = set(required_skills)

    matched = sorted(
        resume_set.intersection(required_set)
    )

    missing = sorted(
        required_set.difference(resume_set)
    )

    if not required_set:
        score = 100
    else:
        score = round(
            len(matched) / len(required_set) * 100
        )

    return {
        "resume_skills": resume_skills,
        "required_skills": required_skills,
        "matched_skills": matched,
        "missing_skills": missing,
        "score": score,
    }


# ============================================================
# OVERALL SCORE
# ============================================================

def calculate_job_match_score(
    skill_score: int,
    keyword_score: int,
    experience_score: int
) -> int:
    """
    Weighted overall job match.

    Skills      = 45%
    Keywords    = 35%
    Experience = 20%
    """

    score = (
        skill_score * 0.45
        + keyword_score * 0.35
        + experience_score * 0.20
    )

    return round(score)


def get_match_level(score: int) -> str:

    if score >= 85:
        return "Excellent Match"

    if score >= 70:
        return "Strong Match"

    if score >= 55:
        return "Moderate Match"

    if score >= 40:
        return "Low Match"

    return "Very Low Match"


# ============================================================
# ANALYSIS EXPLANATION
# ============================================================

def build_analysis(
    skill_result: Dict[str, Any],
    keyword_result: Dict[str, Any],
    experience_result: Dict[str, Any]
) -> Dict[str, List[str]]:

    matched_skills = skill_result["matched_skills"]
    missing_skills = skill_result["missing_skills"]

    matched_keywords = keyword_result["matched_keywords"]
    missing_keywords = keyword_result["missing_keywords"]

    candidate_years = experience_result["candidate_years"]
    required_years = experience_result["required_years"]

    why_you_match = []
    why_you_dont = []
    recommended_skills = []

    # --------------------------------------------------------
    # Match explanation
    # --------------------------------------------------------

    if matched_skills:

        preview = ", ".join(
            matched_skills[:8]
        )

        why_you_match.append(
            f"You already have relevant skills such as {preview}."
        )

    if skill_result["score"] >= 70:

        why_you_match.append(
            "You have a strong foundation of the required technical skills."
        )

    elif skill_result["score"] >= 50:

        why_you_match.append(
            "You have a reasonable foundation of the required technical skills."
        )

    elif skill_result["score"] > 0:

        why_you_match.append(
            "You have some relevant technical skills, but the skill gap is significant."
        )

    if matched_keywords:

        why_you_match.append(
            f"{len(matched_keywords)} important job keywords "
            "are already represented in your resume."
        )

    # --------------------------------------------------------
    # Why not
    # --------------------------------------------------------

    if missing_skills:

        preview = ", ".join(
            missing_skills[:8]
        )

        why_you_dont.append(
            f"Your resume is missing important required skills: {preview}."
        )

    if missing_keywords:

        preview = ", ".join(
            missing_keywords[:8]
        )

        why_you_dont.append(
            f"Some job-specific keywords are not clearly represented: {preview}."
        )

    if required_years > 0:

        if candidate_years < required_years:

            why_you_dont.append(
                f"The job asks for about {required_years} years "
                f"of experience, while the resume indicates about "
                f"{candidate_years} years."
            )

    # --------------------------------------------------------
    # Recommendations
    # --------------------------------------------------------

    for skill in missing_skills:
        if skill not in recommended_skills:
            recommended_skills.append(skill)

    for keyword in missing_keywords:

        if keyword not in recommended_skills:
            recommended_skills.append(keyword)

    # Limit recommendations.
    recommended_skills = recommended_skills[:10]

    if not why_you_match:
        why_you_match.append(
            "Very few direct matches were found between the resume and job description."
        )

    if not why_you_dont:
        why_you_dont.append(
            "No major compatibility gaps were detected."
        )

    return {
        "why_you_match": why_you_match,
        "why_you_dont": why_you_dont,
        "recommended_skills": recommended_skills,
    }


# ============================================================
# MAIN JOB MATCH FUNCTION
# ============================================================

def match_resume_to_job(
    resume_text: str,
    job_description: str
) -> Dict[str, Any]:

    if not resume_text or not str(resume_text).strip():

        return {
            "success": False,
            "error": "Resume text is empty."
        }

    if not job_description or not str(job_description).strip():

        return {
            "success": False,
            "error": "Job description is empty."
        }

    # --------------------------------------------------------
    # Skills
    # --------------------------------------------------------

    skill_result = calculate_skill_match(
        resume_text,
        job_description
    )

    # --------------------------------------------------------
    # Keywords
    # --------------------------------------------------------

    keyword_result = match_keywords(
        resume_text,
        job_description
    )

    total_keywords = len(
        keyword_result["job_keywords"]
    )

    matched_keywords_count = len(
        keyword_result["matched_keywords"]
    )

    if total_keywords == 0:
        keyword_score = 100
    else:
        keyword_score = round(
            matched_keywords_count
            / total_keywords
            * 100
        )

    # --------------------------------------------------------
    # Experience
    # --------------------------------------------------------

    candidate_years = extract_experience_years(
        resume_text
    )

    required_years = extract_required_experience(
        job_description
    )

    experience_result = calculate_experience_score(
        candidate_years,
        required_years
    )

    # --------------------------------------------------------
    # Overall score
    # --------------------------------------------------------

    overall_score = calculate_job_match_score(
        skill_result["score"],
        keyword_score,
        experience_result["score"]
    )

    # --------------------------------------------------------
    # Analysis
    # --------------------------------------------------------

    analysis = build_analysis(
        skill_result,
        keyword_result,
        experience_result
    )

    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    return {
        "success": True,

        "job_match": {
            "score": overall_score,
            "level": get_match_level(overall_score),
        },

        "scores": {
            "job_match_score": overall_score,
            "skill_match": skill_result["score"],
            "keyword_match": keyword_score,
            "experience_match": experience_result["score"],
        },

        "skills": {
            "resume_skills": skill_result["resume_skills"],
            "required_skills": skill_result["required_skills"],
            "matched_skills": skill_result["matched_skills"],
            "missing_skills": skill_result["missing_skills"],
        },

        "keywords": {
            "job_keywords": keyword_result["job_keywords"],
            "matched_keywords": keyword_result["matched_keywords"],
            "missing_keywords": keyword_result["missing_keywords"],
        },

        "experience": experience_result,

        "analysis": analysis,

        "summary": {
            "matched_skills_count": len(
                skill_result["matched_skills"]
            ),

            "required_skills_count": len(
                skill_result["required_skills"]
            ),

            "matched_keywords_count": matched_keywords_count,

            "total_keywords": total_keywords,

            "missing_skills_count": len(
                skill_result["missing_skills"]
            ),

            "missing_keywords_count": len(
                keyword_result["missing_keywords"]
            ),
        },
    }


# ============================================================
# DEMO / TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("AI CAREER COPILOT - ATS JOB MATCH TEST")
    print("=" * 70)

    demo_resume = """
    BCA student and software developer with experience in Python,
    Flask, REST APIs, SQL, Git and GitHub.

    Developed AI applications using Python and Flask.
    Built backend APIs and worked with HTML, CSS and SQL.

    1 year of software development experience.
    """

    demo_job = """
    We are looking for an AI/Backend Engineer.

    Requirements:
    Python, Flask, REST API, SQL, Git, AWS, Docker,
    Cloud and Machine Learning.

    The candidate should have at least 2 years of experience.

    Responsibilities include building scalable backend systems,
    API development, deployment and production software.
    """

    result = match_resume_to_job(
        demo_resume,
        demo_job
    )

    print(
        json.dumps(
            result,
            indent=4
        )
    )

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)