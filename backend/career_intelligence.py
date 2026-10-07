from flask import jsonify
from datetime import datetime
import json
import os
from mongo_store import load_dataset, save_dataset
import re


# ============================================================
# DAY 33 — CAREER INTELLIGENCE ENGINE
# ============================================================


# ============================================================
# CAREER DATABASE
# ============================================================

CAREER_PROFILES = {

    "AI / ML Engineer": {

        "description":
            "Build intelligent systems, machine learning models and AI-powered applications.",

        "skills": {
            "python": 10,
            "machine learning": 10,
            "deep learning": 9,
            "numpy": 7,
            "pandas": 7,
            "scikit-learn": 8,
            "tensorflow": 7,
            "pytorch": 7,
            "sql": 6,
            "git": 5,
            "github": 5,
            "flask": 5,
            "rest api": 5,
            "aws": 4,
            "mlops": 4
        },

        "priority": [
            "Python",
            "Machine Learning",
            "Deep Learning",
            "NumPy",
            "Pandas",
            "Scikit-learn",
            "TensorFlow / PyTorch",
            "SQL",
            "Git & GitHub",
            "MLOps"
        ]
    },

    "Data Scientist": {

        "description":
            "Analyze complex datasets and build predictive models to solve business problems.",

        "skills": {
            "python": 9,
            "sql": 8,
            "pandas": 10,
            "numpy": 8,
            "machine learning": 9,
            "statistics": 9,
            "data analysis": 9,
            "scikit-learn": 8,
            "matplotlib": 6,
            "seaborn": 5,
            "power bi": 5,
            "tableau": 5,
            "git": 4,
            "github": 4
        },

        "priority": [
            "Python",
            "SQL",
            "Pandas",
            "NumPy",
            "Statistics",
            "Machine Learning",
            "Data Analysis",
            "Scikit-learn",
            "Visualization"
        ]
    },

    "Data Analyst": {

        "description":
            "Turn raw data into insights, reports and decisions using analytics tools.",

        "skills": {
            "sql": 10,
            "excel": 9,
            "python": 7,
            "pandas": 8,
            "data analysis": 10,
            "statistics": 8,
            "power bi": 9,
            "tableau": 8,
            "data visualization": 8,
            "git": 3
        },

        "priority": [
            "SQL",
            "Excel",
            "Data Analysis",
            "Power BI",
            "Statistics",
            "Pandas",
            "Data Visualization"
        ]
    },

    "Backend Developer": {

        "description":
            "Design APIs, backend services and scalable application systems.",

        "skills": {
            "python": 9,
            "flask": 8,
            "fastapi": 8,
            "django": 7,
            "rest api": 10,
            "sql": 9,
            "mysql": 8,
            "postgresql": 8,
            "git": 7,
            "github": 6,
            "docker": 6,
            "aws": 5,
            "linux": 6
        },

        "priority": [
            "Python",
            "REST APIs",
            "SQL",
            "Flask / FastAPI",
            "Git & GitHub",
            "Docker",
            "Linux",
            "AWS"
        ]
    },

    "Full Stack Developer": {

        "description":
            "Build complete web applications across frontend, backend and databases.",

        "skills": {
            "html": 7,
            "css": 7,
            "javascript": 9,
            "react": 9,
            "node.js": 8,
            "python": 7,
            "flask": 6,
            "rest api": 8,
            "sql": 7,
            "git": 7,
            "github": 6,
            "docker": 5
        },

        "priority": [
            "HTML",
            "CSS",
            "JavaScript",
            "React",
            "Node.js",
            "REST APIs",
            "SQL",
            "Git & GitHub"
        ]
    },

    "Cloud Engineer": {

        "description":
            "Build, deploy and maintain reliable cloud infrastructure and applications.",

        "skills": {
            "aws": 10,
            "linux": 9,
            "docker": 9,
            "git": 8,
            "github": 7,
            "python": 6,
            "networking": 8,
            "terraform": 8,
            "kubernetes": 9,
            "ci/cd": 8,
            "devops": 9
        },

        "priority": [
            "AWS",
            "Linux",
            "Docker",
            "Networking",
            "Terraform",
            "Kubernetes",
            "CI/CD",
            "DevOps"
        ]
    },

    "Frontend Developer": {
        "description": "Create accessible, responsive interfaces and polished web experiences.",
        "skills": {
            "html": 9,
            "css": 9,
            "javascript": 10,
            "react": 9,
            "typescript": 7,
            "accessibility": 7,
            "testing": 6,
            "git": 7,
            "github": 6
        },
        "priority": [
            "HTML", "CSS", "JavaScript", "React", "TypeScript",
            "Accessibility", "Testing", "Git & GitHub"
        ]
    },

    "DevOps Engineer": {
        "description": "Automate delivery and operate reliable infrastructure for modern software teams.",
        "skills": {
            "linux": 9,
            "networking": 8,
            "git": 8,
            "docker": 10,
            "kubernetes": 9,
            "terraform": 9,
            "ci/cd": 10,
            "aws": 8,
            "monitoring": 7,
            "python": 6
        },
        "priority": [
            "Linux", "Networking", "Docker", "Kubernetes", "Terraform",
            "CI/CD", "AWS", "Monitoring"
        ]
    },

    "Cybersecurity Analyst": {
        "description": "Monitor systems, investigate threats and improve an organization's security posture.",
        "skills": {
            "networking": 9,
            "linux": 8,
            "security fundamentals": 10,
            "siem": 8,
            "incident response": 9,
            "python": 6,
            "sql": 5,
            "risk assessment": 7
        },
        "priority": [
            "Networking", "Linux", "Security Fundamentals", "SIEM",
            "Incident Response", "Python", "Risk Assessment"
        ]
    },

    "Product Manager": {
        "description": "Turn customer problems into clear product strategy, experiments and outcomes.",
        "skills": {
            "product discovery": 10,
            "user research": 9,
            "roadmapping": 9,
            "analytics": 8,
            "experimentation": 8,
            "communication": 9,
            "prioritization": 10,
            "sql": 4
        },
        "priority": [
            "Product Discovery", "User Research", "Prioritization",
            "Roadmapping", "Analytics", "Experimentation", "Communication"
        ]
    }
}


# ============================================================
# SKILL ALIASES
# ============================================================

SKILL_ALIASES = {

    "python": [
        "python",
        "python3"
    ],

    "machine learning": [
        "machine learning",
        "machine-learning",
        "ml"
    ],

    "deep learning": [
        "deep learning",
        "deep-learning"
    ],

    "artificial intelligence": [
        "artificial intelligence",
        "ai"
    ],

    "numpy": [
        "numpy"
    ],

    "pandas": [
        "pandas"
    ],

    "scikit-learn": [
        "scikit-learn",
        "sklearn"
    ],

    "tensorflow": [
        "tensorflow"
    ],

    "pytorch": [
        "pytorch"
    ],

    "sql": [
        "sql"
    ],

    "git": [
        "git"
    ],

    "github": [
        "github",
        "github.com"
    ],

    "flask": [
        "flask"
    ],

    "fastapi": [
        "fastapi"
    ],

    "django": [
        "django"
    ],

    "rest api": [
        "rest api",
        "restful api",
        "rest apis",
        "api development"
    ],

    "aws": [
        "aws",
        "amazon web services"
    ],

    "mlops": [
        "mlops",
        "ml ops"
    ],

    "statistics": [
        "statistics",
        "statistical analysis"
    ],

    "data analysis": [
        "data analysis",
        "data analytics"
    ],

    "data visualization": [
        "data visualization",
        "data visualisation"
    ],

    "matplotlib": [
        "matplotlib"
    ],

    "seaborn": [
        "seaborn"
    ],

    "power bi": [
        "power bi",
        "powerbi"
    ],

    "tableau": [
        "tableau"
    ],

    "excel": [
        "excel",
        "microsoft excel"
    ],

    "html": [
        "html",
        "html5"
    ],

    "css": [
        "css",
        "css3"
    ],

    "javascript": [
        "javascript",
        "js"
    ],

    "react": [
        "react",
        "react.js",
        "reactjs"
    ],

    "node.js": [
        "node.js",
        "nodejs",
        "node"
    ],

    "mysql": [
        "mysql"
    ],

    "postgresql": [
        "postgresql",
        "postgres"
    ],

    "docker": [
        "docker"
    ],

    "linux": [
        "linux"
    ],

    "networking": [
        "networking",
        "computer networks"
    ],

    "terraform": [
        "terraform"
    ],

    "kubernetes": [
        "kubernetes",
        "k8s"
    ],

    "ci/cd": [
        "ci/cd",
        "continuous integration",
        "continuous deployment"
    ],

    "devops": [
        "devops",
        "dev ops"
    ]
}


# ============================================================
# HELPERS
# ============================================================

def normalize_text(value):

    if value is None:
        return ""

    return str(value).strip().lower()


def normalize_skill(value):

    text = normalize_text(value)

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


def safe_list(value):

    if isinstance(value, list):
        return value

    return []


def extract_profile(analysis):

    return {

        "name":
            analysis.get(
                "name",
                analysis.get(
                    "detected_name",
                    ""
                )
            ),

        "email":
            analysis.get(
                "email",
                ""
            ),

        "phone":
            analysis.get(
                "phone",
                ""
            ),

        "linkedin":
            analysis.get(
                "linkedin",
                ""
            ),

        "github":
            analysis.get(
                "github",
                ""
            )
    }


# ============================================================
# NORMALIZE RESUME SKILLS
# ============================================================

def normalize_resume_skills(analysis):

    raw_skills = safe_list(
        analysis.get(
            "skills",
            []
        )
    )

    normalized = set()

    for skill in raw_skills:

        value = normalize_skill(
            skill
        )

        if not value:
            continue

        normalized.add(
            value
        )

        for canonical, aliases in SKILL_ALIASES.items():

            if value == canonical:

                normalized.add(
                    canonical
                )

                continue

            if value in aliases:

                normalized.add(
                    canonical
                )


    # --------------------------------------------------------
    # Inspect text-based resume fields
    # --------------------------------------------------------

    searchable_fields = [

        analysis.get(
            "summary",
            ""
        ),

        analysis.get(
            "profile",
            ""
        ),

        analysis.get(
            "objective",
            ""
        ),

        analysis.get(
            "experience",
            ""
        ),

        analysis.get(
            "education",
            ""
        )
    ]

    combined = " ".join(
        str(value)
        for value in searchable_fields
        if value
    ).lower()


    for canonical, aliases in SKILL_ALIASES.items():

        for alias in aliases:

            if alias.lower() in combined:

                normalized.add(
                    canonical
                )

                break


    return sorted(
        normalized
    )


# ============================================================
# SKILL PRESENT
# ============================================================

def skill_present(
    skill,
    user_skills
):

    canonical = normalize_skill(
        skill
    )

    if canonical in user_skills:

        return True


    aliases = SKILL_ALIASES.get(
        canonical,
        []
    )


    for alias in aliases:

        if normalize_skill(alias) in user_skills:

            return True


    return False


# ============================================================
# CAREER SCORING
# ============================================================

def calculate_career_score(
    profile,
    user_skills,
    analysis,
    career_name
):

    career = CAREER_PROFILES[
        career_name
    ]

    required_skills = career[
        "skills"
    ]

    total_weight = sum(
        required_skills.values()
    )

    matched_weight = 0

    matched = []

    missing = []


    for skill, weight in required_skills.items():

        if skill_present(
            skill,
            user_skills
        ):

            matched_weight += weight

            matched.append(
                skill
            )

        else:

            missing.append(
                skill
            )


    if total_weight:

        skill_score = (
            matched_weight /
            total_weight
        ) * 100

    else:

        skill_score = 0


    # --------------------------------------------------------
    # Resume signals
    # --------------------------------------------------------

    try:

        ats_score = float(
            analysis.get(
                "ats_score",
                0
            ) or 0
        )

    except:

        ats_score = 0


    try:

        strength_score = float(
            analysis.get(
                "resume_strength_score",
                analysis.get(
                    "strength_score",
                    0
                )
            ) or 0
        )

    except:

        strength_score = 0


    try:

        content_score = float(
            analysis.get(
                "content_quality",
                0
            ) or 0
        )

    except:

        content_score = 0


    # --------------------------------------------------------
    # Profile completeness
    # --------------------------------------------------------

    profile_bonus = 0

    if profile.get("linkedin"):

        profile_bonus += 2

    if profile.get("github"):

        profile_bonus += 2

    if profile.get("email"):

        profile_bonus += 1


    # --------------------------------------------------------
    # Final score
    # --------------------------------------------------------

    score = (

        skill_score * 0.80

        +

        ats_score * 0.10

        +

        strength_score * 0.07

        +

        min(
            profile_bonus,
            5
        ) / 5 * 100 * 0.03
    )


    if content_score:

        score += (
            min(
                content_score,
                100
            ) * 0.02
        )


    score = round(
        max(
            0,
            min(
                100,
                score
            )
        )
    )


    # --------------------------------------------------------
    # Match level
    # --------------------------------------------------------

    if score >= 85:

        level = "Excellent Match"

    elif score >= 75:

        level = "Strong Match"

    elif score >= 60:

        level = "Good Potential"

    elif score >= 45:

        level = "Developing"

    else:

        level = "Early Stage"


    return {

        "career":
            career_name,

        "match":
            score,

        "level":
            level,

        "description":
            career["description"],

        "matched_skills":
            matched,

        "missing_skills":
            missing,

        "required_skills":
            list(
                required_skills.keys()
            ),

        "learning_priority":
            career["priority"]
    }


# ============================================================
# SKILL GAP ENGINE
# ============================================================

def build_skill_gap(
    recommendations,
    user_skills
):

    all_missing = {}


    for recommendation in recommendations:

        for skill in recommendation[
            "missing_skills"
        ]:

            all_missing[
                skill
            ] = all_missing.get(
                skill,
                0
            ) + 1


    primary = (

        recommendations[0]

        if recommendations

        else None
    )


    primary_missing = (

        primary["missing_skills"]

        if primary

        else []
    )


    gap = []


    for skill, frequency in all_missing.items():

        if skill in primary_missing:

            priority = "HIGH"

        elif frequency >= 3:

            priority = "MEDIUM"

        else:

            priority = "LOW"


        gap.append({

            "skill":
                skill,

            "priority":
                priority,

            "career_relevance":
                frequency
        })


    priority_order = {

        "HIGH": 0,
        "MEDIUM": 1,
        "LOW": 2
    }


    gap.sort(
        key=lambda item: (
            priority_order[
                item["priority"]
            ],
            -item[
                "career_relevance"
            ]
        )
    )


    return gap[:15]


# ============================================================
# STORAGE
# ============================================================

def get_storage_file():

    backend_dir = os.path.dirname(
        os.path.abspath(__file__)
    )

    project_dir = os.path.dirname(
        backend_dir
    )

    return os.path.join(
        project_dir,
        "career_intelligence.json"
    )


def load_saved_data():

    file_path = get_storage_file()


    try:
        data = load_dataset(file_path, {})


        if isinstance(
            data,
            dict
        ):

            return data


    except Exception as error:

        print(
            f"Career intelligence load error: {error}"
        )


    return {}


def save_saved_data(data):

    file_path = get_storage_file()
    save_dataset(file_path, data)


# ============================================================
# MAIN ENGINE
# ============================================================

def build_career_intelligence(
    username,
    resume_manager
):

    analysis = (
        resume_manager.get_latest_analysis(
            username
        )
    )


    if analysis is None:

        return None


    profile = extract_profile(
        analysis
    )


    user_skills = normalize_resume_skills(
        analysis
    )


    recommendations = []


    for career_name in CAREER_PROFILES:

        recommendation = (
            calculate_career_score(

                profile=profile,

                user_skills=user_skills,

                analysis=analysis,

                career_name=career_name
            )
        )


        recommendations.append(
            recommendation
        )


    recommendations.sort(
        key=lambda item:
            item["match"],
        reverse=True
    )


    primary = (

        recommendations[0]

        if recommendations

        else None
    )


    skill_gap = build_skill_gap(
        recommendations,
        user_skills
    )


    matched_primary = (

        primary["matched_skills"]

        if primary

        else []
    )


    missing_primary = (

        primary["missing_skills"]

        if primary

        else []
    )


    result = {

        "username":
            username,

        "generated_at":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "profile":
            profile,

        "current_skills":
            user_skills,

        "skill_count":
            len(user_skills),

        "resume": {

            "resume_strength":
                analysis.get(
                    "resume_strength_score",
                    analysis.get(
                        "strength_score",
                        0
                    )
                ),

            "ats_score":
                analysis.get(
                    "ats_score",
                    0
                ),

            "content_quality":
                analysis.get(
                    "content_quality",
                    0
                ),

            "achievement_strength":
                analysis.get(
                    "achievement_strength",
                    0
                ),

            "resume_file":
                analysis.get(
                    "resume_file",
                    analysis.get(
                        "resume_name",
                        ""
                    )
                )
        },

        "recommended_career":
            primary,

        "career_recommendations":
            recommendations,

        "skill_gap":
            skill_gap,

        "primary_matched_skills":
            matched_primary,

        "primary_missing_skills":
            missing_primary
    }


    return result


# ============================================================
# ROUTE REGISTRATION
# ============================================================

def register_day33_routes(
    app,
    resume_manager,
    require_auth
):

    # ========================================================
    # MAIN CAREER INTELLIGENCE
    # ========================================================

    @app.route(
        "/api/career-intelligence/<username>",
        methods=["GET"]
    )
    @require_auth
    def career_intelligence(
        username
    ):

        username = str(
            username
        ).strip()


        if not username:

            return jsonify({

                "success":
                    False,

                "message":
                    "Username is required."

            }), 400


        try:

            result = (
                build_career_intelligence(
                    username,
                    resume_manager
                )
            )


            if result is None:

                return jsonify({

                    "success":
                        True,

                    "has_analysis":
                        False,

                    "username":
                        username,

                    "message":
                        "Analyze your resume first to generate career intelligence."

                }), 200


            # ------------------------------------------------
            # Save latest intelligence
            # ------------------------------------------------

            saved = load_saved_data()


            saved[
                username.lower()
            ] = result


            save_saved_data(
                saved
            )


            return jsonify({

                "success":
                    True,

                "has_analysis":
                    True,

                "data":
                    result

            }), 200


        except Exception as error:

            print(
                f"Day 33 career intelligence error: {error}"
            )


            return jsonify({

                "success":
                    False,

                "message":
                    f"Career intelligence failed: {str(error)}"

            }), 500


    # ========================================================
    # SAVED CAREER INTELLIGENCE
    # ========================================================

    @app.route(
        "/api/career-intelligence/saved/<username>",
        methods=["GET"]
    )
    @require_auth
    def saved_career_intelligence(
        username
    ):

        username = str(
            username
        ).strip()


        if not username:

            return jsonify({

                "success":
                    False,

                "message":
                    "Username is required."

            }), 400


        saved = load_saved_data()


        result = saved.get(
            username.lower()
        )


        if result is None:

            return jsonify({

                "success":
                    True,

                "has_data":
                    False,

                "data":
                    None

            }), 200


        return jsonify({

            "success":
                True,

            "has_data":
                True,

            "data":
                result

        }), 200


    # ========================================================
    # CAREER PROFILE DATABASE
    # ========================================================

    @app.route(
        "/api/career-intelligence/careers",
        methods=["GET"]
    )
    def career_profiles():

        careers = []


        for name, data in (
            CAREER_PROFILES.items()
        ):

            careers.append({

                "career":
                    name,

                "description":
                    data["description"],

                "required_skills":
                    list(
                        data["skills"].keys()
                    ),

                "priority":
                    data["priority"]
            })


        return jsonify({

            "success":
                True,

            "careers":
                careers

        }), 200