import os
import re
from copy import deepcopy
from datetime import datetime


class ResumeOptimizer:

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self):

        self.strong_action_verbs = [
            "Built",
            "Developed",
            "Designed",
            "Implemented",
            "Engineered",
            "Created",
            "Automated",
            "Optimized",
            "Analyzed",
            "Deployed",
            "Integrated",
            "Improved",
            "Configured",
            "Tested",
            "Debugged",
            "Migrated",
            "Trained",
            "Evaluated",
            "Researched",
            "Maintained",
            "Coordinated",
            "Solved",
            "Executed",
            "Delivered",
            "Launched",
            "Streamlined",
            "Led",
            "Managed",
            "Architected",
        ]

        self.weak_replacements = {
            "worked on": "Developed",
            "worked with": "Collaborated with",
            "helped with": "Contributed to",
            "helped": "Supported",
            "used": "Utilized",
            "made": "Created",
            "did": "Executed",
            "responsible for": "Managed",
            "handled": "Managed",
            "participated in": "Contributed to",
            "involved in": "Contributed to",
            "assisted": "Supported",
            "learned": "Applied",
            "tried": "Implemented",
        }

        self.generic_replacements = {
            "hardworking": "demonstrated consistent execution",
            "hard working": "demonstrated consistent execution",
            "team player": (
                "collaborated effectively with cross-functional teams"
            ),
            "quick learner": (
                "adapted rapidly to new technologies"
            ),
            "self motivated": "demonstrated strong ownership",
            "self-motivated": "demonstrated strong ownership",
            "passionate": "focused on",
            "dedicated": "committed to",
            "responsible": "accountable for",
            "detail oriented": "detail-oriented",
        }

        self.section_order = [
            "Summary",
            "Professional Summary",
            "Objective",
            "Education",
            "Skills",
            "Technical Skills",
            "Experience",
            "Work Experience",
            "Internship",
            "Projects",
            "Certifications",
            "Achievements",
            "Languages",
            "Interests",
        ]

        self.role_keywords = {

            "AI / ML": [
                "Python",
                "Machine Learning",
                "Artificial Intelligence",
                "Pandas",
                "NumPy",
                "Scikit-learn",
                "TensorFlow",
                "PyTorch",
                "NLP",
                "Computer Vision",
                "Generative AI",
                "LLM",
            ],

            "Python Developer": [
                "Python",
                "Flask",
                "Django",
                "FastAPI",
                "REST API",
                "SQL",
                "Git",
                "GitHub",
                "Docker",
                "Testing",
            ],

            "Data Science": [
                "Python",
                "Pandas",
                "NumPy",
                "Matplotlib",
                "Seaborn",
                "Machine Learning",
                "Data Analysis",
                "SQL",
                "Scikit-learn",
            ],

            "Web Development": [
                "HTML",
                "CSS",
                "JavaScript",
                "React",
                "Node.js",
                "Express.js",
                "SQL",
                "Git",
                "GitHub",
                "REST API",
            ],

            "Software Development": [
                "Python",
                "Java",
                "SQL",
                "Git",
                "GitHub",
                "REST API",
                "Testing",
                "Data Structures",
            ],
        }

    # ============================================================
    # BASIC UTILITIES
    # ============================================================

    def _safe_text(self, value):

        if value is None:
            return ""

        return str(value)

    def clean_text(self, text):

        text = self._safe_text(text)

        text = text.replace("\x00", " ")
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")
        text = text.replace("\u00a0", " ")
        text = text.replace("\u200b", "")
        text = text.replace("\ufeff", "")

        text = re.sub(
            r"[ \t]+",
            " ",
            text
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text
        )

        return text.strip()

    # ============================================================
    # TARGET ROLE DETECTION
    # ============================================================

    def detect_target_role(
        self,
        analysis=None,
        job_description=""
    ):

        analysis = analysis or {}

        job_description = self._safe_text(
            job_description
        )

        # --------------------------------------------------------
        # JOB DESCRIPTION
        # --------------------------------------------------------

        if job_description.strip():

            lower = job_description.lower()

            role_patterns = [

                (
                    "AI / ML",
                    [
                        "machine learning engineer",
                        "ml engineer",
                        "ai engineer",
                        "artificial intelligence engineer",
                        "artificial intelligence",
                        "machine learning",
                        "deep learning",
                        "generative ai",
                        "llm engineer",
                        "llm",
                    ]
                ),

                (
                    "Python Developer",
                    [
                        "python developer",
                        "python engineer",
                        "backend python",
                        "python backend",
                        "backend developer",
                    ]
                ),

                (
                    "Data Science",
                    [
                        "data scientist",
                        "data science",
                        "data analyst",
                        "data analytics",
                    ]
                ),

                (
                    "Web Development",
                    [
                        "frontend developer",
                        "front-end developer",
                        "full stack developer",
                        "full-stack developer",
                        "web developer",
                        "web development",
                    ]
                ),
            ]

            for role, keywords in role_patterns:

                if any(
                    keyword in lower
                    for keyword in keywords
                ):
                    return role

        # --------------------------------------------------------
        # ANALYSIS ROLE COVERAGE
        # --------------------------------------------------------

        role_coverage = analysis.get(
            "role_keyword_coverage",
            {}
        )

        if isinstance(
            role_coverage,
            dict
        ) and role_coverage:

            best_role = None
            best_score = -1

            for role, data in role_coverage.items():

                if not isinstance(
                    data,
                    dict
                ):
                    continue

                score = data.get(
                    "score",
                    0
                )

                try:
                    score = float(score)
                except (
                    TypeError,
                    ValueError
                ):
                    score = 0

                if score > best_score:

                    best_score = score
                    best_role = role

            if best_role:
                return best_role

        # --------------------------------------------------------
        # ANALYSIS SKILLS
        # --------------------------------------------------------

        skills = analysis.get(
            "skills",
            []
        )

        if not isinstance(
            skills,
            list
        ):
            skills = []

        normalized_skills = [
            self._safe_text(skill).strip().lower()
            for skill in skills
        ]

        ai_skills = [
            "machine learning",
            "artificial intelligence",
            "tensorflow",
            "pytorch",
            "scikit-learn",
            "generative ai",
            "llm",
            "deep learning",
        ]

        if any(
            skill in normalized_skills
            for skill in ai_skills
        ):
            return "AI / ML"

        if any(
            skill in normalized_skills
            for skill in [
                "pandas",
                "numpy",
                "data science",
                "data analysis",
            ]
        ):
            return "Data Science"

        if any(
            skill in normalized_skills
            for skill in [
                "react",
                "javascript",
                "html",
                "css",
                "node.js",
            ]
        ):
            return "Web Development"

        if "python" in normalized_skills:
            return "Python Developer"

        return "Software Development"

    # ============================================================
    # ACTION VERBS
    # ============================================================

    def improve_action_verbs(self, text):

        optimized = self._safe_text(text)

        replacements = sorted(
            self.weak_replacements.items(),
            key=lambda item: len(item[0]),
            reverse=True
        )

        changes = []

        for weak, strong in replacements:

            pattern = (
                r"\b"
                + re.escape(weak)
                + r"\b"
            )

            if re.search(
                pattern,
                optimized,
                re.IGNORECASE
            ):

                optimized = re.sub(
                    pattern,
                    strong,
                    optimized,
                    flags=re.IGNORECASE
                )

                changes.append({
                    "original": weak,
                    "replacement": strong,
                    "type": "action_verb"
                })

        return optimized, changes

    # ============================================================
    # GENERIC LANGUAGE
    # ============================================================

    def improve_generic_language(self, text):

        optimized = self._safe_text(text)

        changes = []

        replacements = sorted(
            self.generic_replacements.items(),
            key=lambda item: len(item[0]),
            reverse=True
        )

        for generic, replacement in replacements:

            pattern = (
                r"\b"
                + re.escape(generic)
                + r"\b"
            )

            if re.search(
                pattern,
                optimized,
                re.IGNORECASE
            ):

                optimized = re.sub(
                    pattern,
                    replacement,
                    optimized,
                    flags=re.IGNORECASE
                )

                changes.append({
                    "original": generic,
                    "replacement": replacement,
                    "type": "generic_language"
                })

        return optimized, changes

    # ============================================================
    # BULLET STRUCTURE
    # ============================================================

    def improve_bullet_structure(self, text):

        lines = self.clean_text(
            text
        ).splitlines()

        optimized_lines = []

        changes = []

        bullet_pattern = (
            r"^[•\-*▪●◦]+\s*"
        )

        for line in lines:

            stripped = line.strip()

            if not stripped:

                optimized_lines.append("")
                continue

            if re.match(
                bullet_pattern,
                stripped
            ):

                content = re.sub(
                    bullet_pattern,
                    "",
                    stripped
                )

                if content:

                    content = re.sub(
                        r"^(I|My|We)\s+",
                        "",
                        content,
                        flags=re.IGNORECASE
                    )

                    new_line = (
                        "• "
                        + content
                    )

                    optimized_lines.append(
                        new_line
                    )

                    if stripped != new_line:

                        changes.append({
                            "original": stripped,
                            "replacement": new_line,
                            "type": "bullet_format"
                        })

            else:

                optimized_lines.append(
                    stripped
                )

        return (
            "\n".join(optimized_lines),
            changes
        )

    # ============================================================
    # FIND SECTION
    # ============================================================

    def _normalize_section_name(self, line):

        normalized = re.sub(
            r"[^a-zA-Z ]",
            " ",
            self._safe_text(line).lower()
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized
        ).strip()

        return normalized

    def find_section_range(
        self,
        text,
        section_name
    ):

        lines = self.clean_text(
            text
        ).splitlines()

        normalized_target = (
            self._normalize_section_name(
                section_name
            )
        )

        start = None
        end = len(lines)

        for index, line in enumerate(lines):

            normalized = (
                self._normalize_section_name(
                    line
                )
            )

            if normalized == normalized_target:

                start = index
                break

        if start is None:

            return (
                None,
                None,
                lines
            )

        section_names = [

            self._normalize_section_name(
                section
            )

            for section in self.section_order

            if self._normalize_section_name(
                section
            ) != normalized_target
        ]

        for index in range(
            start + 1,
            len(lines)
        ):

            normalized = (
                self._normalize_section_name(
                    lines[index]
                )
            )

            if normalized in section_names:

                end = index
                break

        return (
            start,
            end,
            lines
        )

    # ============================================================
    # SUMMARY GENERATION
    # ============================================================

    def generate_summary(
        self,
        original_text,
        analysis,
        target_role
    ):

        skills = analysis.get(
            "skills",
            []
        )

        if not isinstance(
            skills,
            list
        ):
            skills = []

        cleaned_skills = []

        for skill in skills:

            skill = self._safe_text(
                skill
            ).strip()

            if skill:

                cleaned_skills.append(
                    skill
                )

        skill_text = ", ".join(
            cleaned_skills[:8]
        )

        if not skill_text:

            skill_text = (
                "relevant technical technologies"
            )

        experience_text = ""

        experience = analysis.get(
            "experience",
            []
        )

        if isinstance(
            experience,
            list
        ) and experience:

            experience_text = (
                "with practical experience in "
            )

        summary = (
            f"{target_role} candidate "
            f"{experience_text}"
            f"with hands-on experience in "
            f"{skill_text}. "
            f"Demonstrated ability to build practical "
            f"projects, apply technical concepts, "
            f"solve development problems, and "
            f"deliver structured technical solutions."
        )

        return summary

    # ============================================================
    # IMPROVE SUMMARY
    # ============================================================

    def improve_summary_section(
        self,
        text,
        analysis,
        target_role
    ):

        start, end, lines = (
            self.find_section_range(
                text,
                "Summary"
            )
        )

        summary = self.generate_summary(
            text,
            analysis,
            target_role
        )

        if start is None:

            # Also check Professional Summary

            start, end, lines = (
                self.find_section_range(
                    text,
                    "Professional Summary"
                )
            )

        if start is None:

            lines = [

                "Summary",

                summary,

                "",

            ] + lines

            return (
                "\n".join(lines),
                {
                    "type": "summary_added",
                    "message":
                        "Professional Summary added."
                }
            )

        new_lines = (
            lines[:start + 1]
            + [summary]
            + lines[end:]
        )

        return (
            "\n".join(new_lines),
            {
                "type": "summary_improved",
                "message":
                    "Professional Summary improved."
            }
        )

    # ============================================================
    # IMPROVE PROJECTS
    # ============================================================

    def improve_projects_section(
        self,
        text
    ):

        start, end, lines = (
            self.find_section_range(
                text,
                "Projects"
            )
        )

        if start is None:

            return (
                text,
                []
            )

        project_lines = lines[
            start + 1:end
        ]

        improved = []

        changes = []

        for line in project_lines:

            stripped = line.strip()

            if not stripped:

                improved.append("")
                continue

            if re.match(
                r"^[•\-*▪●◦]+\s*",
                stripped
            ):

                content = re.sub(
                    r"^[•\-*▪●◦]+\s*",
                    "",
                    stripped
                )

                if content:

                    new_line = (
                        "• "
                        + content
                    )

                    improved.append(
                        new_line
                    )

                    if stripped != new_line:

                        changes.append({
                            "type":
                                "projects_format",
                            "original":
                                stripped,
                            "replacement":
                                new_line,
                        })

            else:

                improved.append(
                    stripped
                )

        new_lines = (
            lines[:start + 1]
            + improved
            + lines[end:]
        )

        if not changes:

            changes.append({
                "type":
                    "projects_format",
                "message":
                    "Project descriptions checked for clarity."
            })

        return (
            "\n".join(new_lines),
            changes
        )

    # ============================================================
    # ROLE KEYWORDS
    # ============================================================

    def get_role_keywords(
        self,
        target_role,
        analysis=None
    ):

        analysis = analysis or {}

        role_data = analysis.get(
            "role_keyword_coverage",
            {}
        )

        if isinstance(
            role_data,
            dict
        ):

            if target_role in role_data:

                role_info = role_data[
                    target_role
                ]

                if isinstance(
                    role_info,
                    dict
                ):

                    missing = role_info.get(
                        "missing_keywords",
                        []
                    )

                    if isinstance(
                        missing,
                        list
                    ):

                        return missing

        return self.role_keywords.get(
            target_role,
            []
        )

    # ============================================================
    # KEYWORD SUGGESTIONS
    # ============================================================

    def generate_keyword_suggestions(
        self,
        text,
        analysis,
        target_role
    ):

        missing = self.get_role_keywords(
            target_role,
            analysis
        )

        lower_text = (
            self._safe_text(text).lower()
        )

        suggestions = []

        for keyword in missing:

            keyword_text = (
                self._safe_text(
                    keyword
                ).strip()
            )

            if not keyword_text:
                continue

            if keyword_text.lower() not in lower_text:

                suggestions.append(
                    keyword_text
                )

        return suggestions[:15]

    # ============================================================
    # JOB DESCRIPTION KEYWORDS
    # ============================================================

    def extract_job_keywords(
        self,
        job_description,
        target_role
    ):

        job_description = self._safe_text(
            job_description
        )

        if not job_description.strip():

            return []

        known_keywords = set(
            self.role_keywords.get(
                target_role,
                []
            )
        )

        text_lower = job_description.lower()

        found = []

        for keyword in known_keywords:

            if keyword.lower() in text_lower:

                found.append(
                    keyword
                )

        # Additional common technical terms

        common_terms = [

            "Python",
            "Java",
            "JavaScript",
            "TypeScript",
            "SQL",
            "Git",
            "GitHub",
            "Docker",
            "AWS",
            "Azure",
            "GCP",
            "Flask",
            "Django",
            "FastAPI",
            "React",
            "Node.js",
            "REST API",
            "Machine Learning",
            "Deep Learning",
            "NLP",
            "Computer Vision",
            "Generative AI",
            "LLM",
            "Pandas",
            "NumPy",
            "Scikit-learn",
            "TensorFlow",
            "PyTorch",
        ]

        for keyword in common_terms:

            if (
                keyword.lower()
                in text_lower
                and
                keyword not in found
            ):

                found.append(
                    keyword
                )

        return found[:25]

    # ============================================================
    # JOB KEYWORD SUGGESTIONS
    # ============================================================

    def generate_job_keyword_suggestions(
        self,
        resume_text,
        job_description,
        target_role
    ):

        resume_lower = (
            self._safe_text(
                resume_text
            ).lower()
        )

        job_keywords = (
            self.extract_job_keywords(
                job_description,
                target_role
            )
        )

        missing = []

        for keyword in job_keywords:

            if keyword.lower() not in resume_lower:

                missing.append(
                    keyword
                )

        return missing[:15]

    # ============================================================
    # BUILD IMPROVEMENTS
    # ============================================================

    def build_improvements(
        self,
        original_text,
        optimized_text,
        changes,
        analysis,
        target_role,
        job_description=""
    ):

        improvements = []

        # --------------------------------------------------------
        # LANGUAGE
        # --------------------------------------------------------

        language_changes = [

            change

            for change in changes

            if isinstance(change, dict)

            and change.get("type")
            in [
                "action_verb",
                "generic_language",
            ]
        ]

        if language_changes:

            improvements.append({

                "category":
                    "Language",

                "title":
                    "Stronger professional language",

                "details":
                    f"{len(language_changes)} language "
                    "improvements were applied.",

                "count":
                    len(language_changes),

            })

        # --------------------------------------------------------
        # SUMMARY
        # --------------------------------------------------------

        improvements.append({

            "category":
                "Summary",

            "title":
                "Role-focused professional summary",

            "details":
                f"Summary optimized for the "
                f"{target_role} career direction."

        })

        # --------------------------------------------------------
        # PROJECTS
        # --------------------------------------------------------

        project_changes = [

            change

            for change in changes

            if isinstance(change, dict)

            and change.get("type")
            == "projects_format"
        ]

        if project_changes:

            improvements.append({

                "category":
                    "Projects",

                "title":
                    "Project formatting improved",

                "details":
                    "Project bullet formatting was "
                    "standardized for readability."

            })

        # --------------------------------------------------------
        # ATS KEYWORDS
        # --------------------------------------------------------

        keyword_suggestions = (
            self.generate_keyword_suggestions(
                original_text,
                analysis,
                target_role
            )
        )

        if keyword_suggestions:

            improvements.append({

                "category":
                    "ATS",

                "title":
                    "Role-specific keywords identified",

                "details":
                    "Review the suggested keywords and "
                    "add only keywords that genuinely "
                    "represent your experience.",

                "keywords":
                    keyword_suggestions

            })

        # --------------------------------------------------------
        # JOB DESCRIPTION KEYWORDS
        # --------------------------------------------------------

        job_missing = (
            self.generate_job_keyword_suggestions(
                original_text,
                job_description,
                target_role
            )
        )

        if job_missing:

            improvements.append({

                "category":
                    "Job Match",

                "title":
                    "Job-specific keywords identified",

                "details":
                    "These keywords appear in the job "
                    "description but were not detected "
                    "in the resume.",

                "keywords":
                    job_missing

            })

        # --------------------------------------------------------
        # METRICS
        # --------------------------------------------------------

        metric_count = analysis.get(
            "metric_count",
            0
        )

        try:

            metric_count = int(
                metric_count
            )

        except (
            TypeError,
            ValueError
        ):

            metric_count = 0

        if metric_count < 3:

            improvements.append({

                "category":
                    "Achievements",

                "title":
                    "More measurable impact recommended",

                "details":
                    "Add genuine numbers, percentages, "
                    "scale, accuracy, performance, users, "
                    "time saved or other measurable outcomes. "
                    "Do not invent metrics."

            })

        return improvements

    # ============================================================
    # OPTIMIZE
    # ============================================================

    def optimize(
        self,
        original_text,
        analysis=None,
        target_role="",
        job_description=""
    ):

        # --------------------------------------------------------
        # CLEAN INPUT
        # --------------------------------------------------------

        original_text = self.clean_text(
            original_text
        )

        if not original_text:

            return {

                "success":
                    False,

                "message":
                    "No resume text was provided."

            }

        analysis = deepcopy(
            analysis or {}
        )

        if not isinstance(
            analysis,
            dict
        ):

            analysis = {}

        # --------------------------------------------------------
        # DETECT ROLE
        # --------------------------------------------------------

        if not target_role:

            target_role = (
                self.detect_target_role(
                    analysis=analysis,
                    job_description=job_description
                )
            )

        target_role = (
            self._safe_text(
                target_role
            ).strip()
        )

        if not target_role:

            target_role = (
                "Software Development"
            )

        # --------------------------------------------------------
        # STEP 1 — ACTION VERBS
        # --------------------------------------------------------

        optimized_text, verb_changes = (
            self.improve_action_verbs(
                original_text
            )
        )

        # --------------------------------------------------------
        # STEP 2 — GENERIC LANGUAGE
        # --------------------------------------------------------

        optimized_text, generic_changes = (
            self.improve_generic_language(
                optimized_text
            )
        )

        all_changes = (
            verb_changes
            + generic_changes
        )

        # --------------------------------------------------------
        # STEP 3 — BULLET FORMATTING
        # --------------------------------------------------------

        optimized_text, bullet_changes = (
            self.improve_bullet_structure(
                optimized_text
            )
        )

        all_changes.extend(
            bullet_changes
        )

        # --------------------------------------------------------
        # STEP 4 — SUMMARY
        # --------------------------------------------------------

        optimized_text, summary_change = (
            self.improve_summary_section(
                optimized_text,
                analysis,
                target_role
            )
        )

        all_changes.append(
            summary_change
        )

        # --------------------------------------------------------
        # STEP 5 — PROJECTS
        # --------------------------------------------------------

        optimized_text, project_changes = (
            self.improve_projects_section(
                optimized_text
            )
        )

        all_changes.extend(
            project_changes
        )

        # --------------------------------------------------------
        # ATS KEYWORDS
        # --------------------------------------------------------

        keyword_suggestions = (
            self.generate_keyword_suggestions(
                original_text,
                analysis,
                target_role
            )
        )

        job_keyword_suggestions = (
            self.generate_job_keyword_suggestions(
                original_text,
                job_description,
                target_role
            )
        )

        # --------------------------------------------------------
        # IMPROVEMENTS
        # --------------------------------------------------------

        improvements = (
            self.build_improvements(
                original_text,
                optimized_text,
                all_changes,
                analysis,
                target_role,
                job_description
            )
        )

        # --------------------------------------------------------
        # COUNTS
        # --------------------------------------------------------

        original_word_count = len(
            original_text.split()
        )

        optimized_word_count = len(
            optimized_text.split()
        )

        # --------------------------------------------------------
        # CHANGE SUMMARY
        # --------------------------------------------------------

        change_summary = {

            "action_verb_changes":
                len(verb_changes),

            "generic_language_changes":
                len(generic_changes),

            "bullet_format_changes":
                len(bullet_changes),

            "project_format_changes":
                len(project_changes),

            "total_changes":
                len(all_changes),

        }

        # --------------------------------------------------------
        # RESULT
        # --------------------------------------------------------

        return {

            "success":
                True,

            "target_role":
                target_role,

            "original_resume":
                original_text,

            "optimized_resume":
                optimized_text,

            "original_text":
                original_text,

            "optimized_text":
                optimized_text,

            "original_word_count":
                original_word_count,

            "optimized_word_count":
                optimized_word_count,

            "changes":
                all_changes,

            "change_count":
                len(all_changes),

            "change_summary":
                change_summary,

            "improvements":
                improvements,

            "keyword_suggestions":
                keyword_suggestions,

            "job_keyword_suggestions":
                job_keyword_suggestions,

            "job_keywords_detected":
                self.extract_job_keywords(
                    job_description,
                    target_role
                ),

            "approval_required":
                True,

            "original_preserved":
                True,

            "ai_generated_metrics":
                False,

            "ai_generated_experience":
                False,

            "ai_generated_credentials":
                False,

            "generated_metrics":
                False,

            "generated_experience":
                False,

            "generated_credentials":
                False,

            "message":
                "Resume optimization completed. "
                "Review the optimized version before approval."

        }

    # ============================================================
    # SAVE APPROVED COPY
    # ============================================================

    def save_approved_copy(
        self,
        optimized_text,
        original_filename,
        username,
        output_directory
    ):

        optimized_text = self.clean_text(
            optimized_text
        )

        if not optimized_text:

            raise ValueError(
                "Optimized resume text is empty."
            )

        username = (
            self._safe_text(
                username
            ).strip()
            or "user"
        )

        original_filename = (
            self._safe_text(
                original_filename
            ).strip()
            or "resume.txt"
        )

        output_directory = (
            self._safe_text(
                output_directory
            ).strip()
        )

        if not output_directory:

            raise ValueError(
                "Output directory is required."
            )

        os.makedirs(
            output_directory,
            exist_ok=True
        )

        # --------------------------------------------------------
        # SAFE USERNAME
        # --------------------------------------------------------

        safe_username = re.sub(
            r"[^a-zA-Z0-9_-]+",
            "_",
            username
        ).strip("_")

        if not safe_username:

            safe_username = "user"

        # --------------------------------------------------------
        # SAFE BASE NAME
        # --------------------------------------------------------

        base_name = os.path.splitext(
            os.path.basename(
                original_filename
            )
        )[0]

        base_name = re.sub(
            r"[^a-zA-Z0-9_-]+",
            "_",
            base_name
        ).strip("_")

        if not base_name:

            base_name = "resume"

        # --------------------------------------------------------
        # TIMESTAMP
        # --------------------------------------------------------

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        filename = (
            f"{safe_username}_"
            f"{base_name}_"
            f"optimized_"
            f"{timestamp}.txt"
        )

        output_path = os.path.join(
            output_directory,
            filename
        )

        # --------------------------------------------------------
        # SAVE
        # --------------------------------------------------------

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                optimized_text
            )

        return filename

    # ============================================================
    # OPTIONAL COMPATIBILITY ALIAS
    # ============================================================

    def optimize_text(
        self,
        original_text,
        target_role="",
        job_description="",
        analysis=None
    ):

        return self.optimize(
            original_text=original_text,
            analysis=analysis,
            target_role=target_role,
            job_description=job_description
        )